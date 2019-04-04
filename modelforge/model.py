from copy import deepcopy
import inspect
import logging
import os
from pprint import pformat
import re
import shutil
import tempfile
from typing import BinaryIO, Iterable, List, Optional, Tuple, Union
import uuid

import asdf
import humanize
import numpy
import pygtrie
import scipy.sparse

import modelforge.configuration as config
from modelforge.environment import collect_environment
from modelforge.meta import check_license, format_datetime, generate_new_meta, get_datetime_now
from modelforge.storage_backend import StorageBackend


class Model:
    """
    Base class for all the models. All models should be backwards compatible: \
    base class should be able to load the file generated from an inheritor.
    """

    # The following fields *must* be defined in inherited classes
    NAME = None  #: Name of the model. Used as the logging domain, too.
    VENDOR = None  #: The name of the issuing vendor, e.g. "source{d}"
    DESCRIPTION = None  #: Description of the model, Markdown-formatted

    # The following fields *can* be defined in inherited classes
    LICENSE = "Proprietary"  #: License identifier (according to SPDX)
    NO_COMPRESSION = tuple()  #: Tree path prefixes which should not be compressed.
    # Note: "/" is automatically appended to all the compared paths.
    # Paths always start with a "/".

    # The following fields *should not* be normally touched
    DEFAULT_NAME = "default"  #: When no uuid is specified, this is used.
    DEFAULT_FILE_EXT = ".asdf"  #: File extension of the model.
    ARRAY_COMPRESSION = "lz4"  #: ASDF default compression, options: zlib, bzp2, lz4.
    GENERIC_NAME = "generic"  #: Special name which allows to load any model.

    def __init__(self, **kwargs):
        """
        Initialize a new Model instance.

        :param kwargs: Everything is ignored except ``log_level``.
        """
        assert self.NAME is not None
        assert self.VENDOR is not None
        assert self.DESCRIPTION is not None
        self._log = logging.getLogger(self.NAME)
        self._log.setLevel(kwargs.get("log_level", logging.DEBUG))
        self._source = None
        self._meta = generate_new_meta(self.NAME, self.DESCRIPTION, self.VENDOR, self.LICENSE)
        self._asdf = None
        self._size = 0
        self._initial_version = None
        assert isinstance(self.NO_COMPRESSION, tuple), "NO_COMPRESSION must be a tuple"
        self._compression_prefixes = pygtrie.PrefixSet(self.NO_COMPRESSION)

    def load(self, source: Union[str, BinaryIO, "Model"]=None, cache_dir: str=None,
             backend: StorageBackend=None, lazy=False) -> "Model":
        """
        Build a new Model instance.

        :param source: UUID, file system path, file object or an URL; None means auto.
        :param cache_dir: The directory where to store the downloaded model.
        :param backend: Remote storage backend to use if ``source`` is a UUID or a URL.
        :param lazy: Do not really load numpy arrays into memory. Instead, mmap() them. \
                     User is expected to call Model.close() when the tree is no longer needed.
        """
        if isinstance(source, Model):
            if not isinstance(source, type(self)):
                raise TypeError("Incompatible model instance: %s <> %s" %
                                (type(source), type(self)))
            self.__dict__ = source.__dict__
            return self

        if backend is not None and not isinstance(backend, StorageBackend):
            raise TypeError("backend must be an instance of "
                            "modelforge.storage_backend.StorageBackend")
        self._source = str(source)
        generic = self.NAME == self.GENERIC_NAME
        try:
            if source is None or (isinstance(source, str) and not os.path.isfile(source)):
                if cache_dir is None:
                    if not generic:
                        cache_dir = os.path.join(self.cache_dir(), self.NAME)
                    else:
                        cache_dir = tempfile.mkdtemp(prefix="modelforge-")
                try:
                    uuid.UUID(source)
                    is_uuid = True
                except (TypeError, ValueError):
                    is_uuid = False
                model_id = self.DEFAULT_NAME if not is_uuid else source
                file_name = model_id + self.DEFAULT_FILE_EXT
                file_name = os.path.join(os.path.expanduser(cache_dir), file_name)
                if os.path.exists(file_name) and (not source or not os.path.exists(source)):
                    source = file_name
                elif source is None or is_uuid:
                    if backend is None:
                        raise ValueError("The backend must be set to load a UUID or the default "
                                         "model.")
                    index = backend.index.contents
                    config = index["models"]
                    if not generic:
                        if not is_uuid:
                            model_id = index["meta"][self.NAME][model_id]
                        source = config[self.NAME][model_id]
                    else:
                        if not is_uuid:
                            raise ValueError("File path, URL or UUID is needed.")
                        for models in config.values():
                            if source in models:
                                source = models[source]
                                break
                        else:
                            raise FileNotFoundError("Model %s not found." % source)
                    source = source["url"]
                if re.match(r"\w+://", source):
                    if backend is None:
                        raise ValueError("The backend must be set to load a URL.")
                    backend.fetch_model(source, file_name)
                    self._source = source
                    source = file_name
            if isinstance(source, str):
                size = os.stat(source).st_size
            else:
                self._source = "<file object>"
                pos = source.tell()
                size = source.seek(0, os.SEEK_END) - pos
                source.seek(pos, os.SEEK_SET)
            self._log.info("Reading %s (%s)...", source, humanize.naturalsize(size))
            model = asdf.open(source, copy_arrays=not lazy, lazy_load=lazy)
            try:
                tree = model.tree
                self._meta = tree["meta"]
                self._initial_version = list(self.version)
                if not generic:
                    meta_name = self._meta["model"]
                    matched = self.NAME == meta_name
                    if not matched:
                        needed = {self.NAME}
                        for child in type(self).__subclasses__():
                            needed.add(child.NAME)
                            matched |= child.NAME == meta_name
                        if not matched:
                            raise ValueError(
                                "The supplied model is of the wrong type: needed "
                                "%s, got %s." % (needed, meta_name))
                self._load_tree(tree)
            finally:
                if not lazy:
                    model.close()
                else:
                    self._asdf = model
        finally:
            if generic and cache_dir is not None:
                shutil.rmtree(cache_dir)
        self._size = size
        return self

    @property
    def meta(self):
        """
        Metadata dictionary: when was created, uuid, version, etc.
        """
        return self._meta

    @property
    def source(self):
        """
        Return the source of the model (URL or file name).
        """
        return self._source

    @property
    def size(self):
        """
        Return the size of the serialized model.
        """
        return self._size

    def metaprop(name: str, doc: str, readonly=False):
        """Temporary property builder."""
        def get(self):
            return self.meta[name]
        get.__doc__ = "Get %s%s." % (doc, " (readonly)" if readonly else "")

        if not readonly:
            def set(self, value):
                self.meta[name] = value
            set.__doc__ = "Set %s." % doc

            return property(get, set)
        return property(get)

    code = metaprop("code", "usage code example")
    created_at = metaprop("created_at", "date and time when the model was created", readonly=True)
    datasets = metaprop("datasets", "list of the datasets used to generate the model")
    description = metaprop("description", "description of the model, Markdown format")
    vendor = metaprop("vendor", "name of the party responsible for support")
    environment = metaprop(
        "environment",
        "the version of the Python interpreter, the details about running OS and "
        "the list of packages used to create the model",
        readonly=True)
    extra = metaprop("extra", "additional information which is not covered by other fields")
    license = metaprop("license", "license of the model (SPDX identifier or \"Proprietary\")")
    metrics = metaprop("metrics", "achieved quality metric values")
    name = metaprop("model", "type identifier of the model", readonly=True)
    parent = metaprop("parent", "UUID of the previous model", readonly=True)
    references = metaprop("references", "list of the related URLs")
    series = metaprop("series", "subtype of the model")
    tags = metaprop("tags", "categories for classification")
    uuid = metaprop("uuid", "unique identifier of the model instance", readonly=True)
    version = metaprop("version", "version of the model: semver or single number", readonly=True)

    del metaprop

    def close(self):
        """
        *Effective only if the model is loaded in lazy mode = `load(lazy=True)`* \
        Free all the allocated resources for the underlying ASDF file.

        :return: Nothing.
        """
        if self._asdf is not None:
            self._asdf.close()

    def derive(self, new_version: Union[tuple, list]=None) -> "Model":
        """
        Inherit the new model from the current one - used for versioning. \
        This operation is in-place.

        :param new_version: The version of the new model.
        :return: The derived model - self.
        """
        meta = self.meta
        first_time = self._initial_version == self.version
        if new_version is None:
            new_version = meta["version"]
            new_version[-1] += 1
        if not isinstance(new_version, (tuple, list)):
            raise ValueError("new_version must be either a list or a tuple, got %s"
                             % type(new_version))
        meta["version"] = list(new_version)
        if first_time:
            meta["parent"] = meta["uuid"]
        meta["uuid"] = str(uuid.uuid4())
        return self

    def __str__(self):
        """Format model description as a string."""
        try:
            dump = self.dump()
        except NotImplementedError:
            dump = ""
        except AttributeError:
            return repr(self)
        if dump:
            dump = "\n" + dump
        meta = deepcopy(self.meta)
        meta["created_at"] = format_datetime(meta["created_at"])
        meta["size"] = humanize.naturalsize(self.size)
        try:
            meta["environment"]["packages"] = \
                " ".join("%s==%s" % tuple(p) for p in self.environment["packages"])
        except KeyError:
            pass
        return "%s%s" % (pformat(meta, width=1024), dump)

    def __repr__(self):
        """Format model object as a string."""
        module = inspect.getmodule(self)
        module_name = module.__name__
        if module_name == "__main__":
            if module.__spec__ is not None:
                module_name = module.__spec__.name
            else:
                try:
                    module_name = "[%s]" % os.path.abspath(module.__file__)
                except AttributeError:
                    module_name = "[unknown]"
        return "%s.%s().load(source=%s)" % (
            module_name, type(self).__name__,
            '"%s"' % self._source if self._source is not None else None)

    def __getstate__(self):
        """
        Fix pickling.
        """
        state = {
            "_log": self._log.level,
            "_meta": self._meta,
            "_source": self._source,
            "_size": self._size,
            "_initial_version": self._initial_version,
            "tree": self._generate_tree()
        }
        # ensure that there are no ndarray proxies which cannot be pickled
        queue = [(None, None, state["tree"])]
        while queue:
            parent, key, element = queue.pop()
            if isinstance(element, dict):
                for key, val in element.items():
                    queue.append((element, key, val))
            elif isinstance(element, (list, tuple)):
                for i, child in enumerate(element):
                    queue.append((element, i, child))
            elif isinstance(element, asdf.tags.core.ndarray.NDArrayType):
                parent[key] = element.__array__()
        return state

    def __setstate__(self, state):
        """
        Fix unpickling.
        """
        log_level = state["_log"]
        self._log = logging.getLogger(self.NAME)
        self._log.setLevel(log_level)
        self._asdf = None
        for key in ("_meta", "_source", "_size", "_initial_version"):
            setattr(self, key, state[key])
        self._compression_prefixes = pygtrie.PrefixSet(self.NO_COMPRESSION)
        self._load_tree(state["tree"])

    @staticmethod
    def cache_dir() -> str:
        """Return the default cache directory where downloaded models are stored."""
        if config.VENDOR is None:
            raise RuntimeError("modelforge is not configured; look at modelforge.configuration. "
                               "Depending on your objective you may or may not want to create a "
                               "modelforgecfg.py file which sets VENDOR and the rest.")
        return os.path.join("~", "." + config.VENDOR)

    def get_dep(self, name: str) -> str:
        """
        Return the uuid of the dependency identified with "name".

        :param name:
        :return: UUID
        """
        deps = self.meta["dependencies"]
        for d in deps:
            if d["model"] == name:
                return d
        raise KeyError("%s not found in %s." % (name, deps))

    def set_dep(self, *deps) -> "Model":
        """
        Register the dependencies for this model.

        :param deps: The parent models: objects or meta dicts.
        :return: self
        """
        self.meta["dependencies"] = [
            (d.meta if not isinstance(d, dict) else d) for d in deps]
        return self

    def dump(self) -> str:
        """
        Return the string with the brief information about the model. \
        Should not include any metadata.
        """
        raise NotImplementedError()

    def save(self, output: Union[str, BinaryIO], series: Optional[str] = None,
             deps: Iterable=tuple(), create_missing_dirs: bool=True) -> "Model":
        """
        Serialize the model to a file.

        :param output: Path to the file or a file object.
        :param series: Name of the model series. If it is None, it will be taken from \
                       the current value; if the current value is empty, an error is raised.
        :param deps: List of the dependencies.
        :param create_missing_dirs: create missing directories in output path if the output is a \
                                    path.
        :return: self
        """
        check_license(self.license)
        if series is None:
            if self.series is None:
                raise ValueError("series must be specified")
        else:
            self.series = series
        if isinstance(output, str) and create_missing_dirs:
            dirs = os.path.split(output)[0]
            if dirs:
                os.makedirs(dirs, exist_ok=True)
        self.set_dep(*deps)
        tree = self._generate_tree()
        self._write_tree(tree, output)
        self._initial_version = self.version
        return self

    def _write_tree(self, tree: dict, output: Union[str, BinaryIO], file_mode: int=0o666) -> None:
        """
        Write the model to disk.

        :param tree: The data dict - will be the ASDF tree.
        :param output: The output file path or a file object.
        :param file_mode: The output file's permissions.
        :return: None
        """
        self.meta["created_at"] = get_datetime_now()
        meta = self.meta.copy()
        meta["environment"] = collect_environment()
        final_tree = {}
        final_tree.update(tree)
        final_tree["meta"] = meta
        isfileobj = not isinstance(output, str)
        if not isfileobj:
            self._source = output
            path = output
            output = open(output, "wb")
            os.chmod(path, file_mode)
            pos = 0
        else:
            pos = output.tell()
        try:
            with asdf.AsdfFile(final_tree) as file:
                queue = [("", tree)]
                while queue:
                    path, element = queue.pop()
                    if isinstance(element, dict):
                        for key, val in element.items():
                            queue.append((path + "/" + key, val))
                    elif isinstance(element, (list, tuple)):
                        for child in element:
                            queue.append((path, child))
                    elif isinstance(element, numpy.ndarray):
                        path += "/"
                        if path not in self._compression_prefixes:
                            self._log.debug("%s -> %s compression", path, self.ARRAY_COMPRESSION)
                            file.set_array_compression(element, self.ARRAY_COMPRESSION)
                        else:
                            self._log.debug("%s -> compression disabled", path)
                file.write_to(output)
            self._size = output.seek(0, os.SEEK_END) - pos
        finally:
            if not isfileobj:
                output.close()

    def _generate_tree(self) -> dict:
        """
        Return the tree to store in ASDF file.

        :return: None
        """
        raise NotImplementedError()

    def _load_tree(self, tree: dict) -> None:
        """
        Attach the needed data from the tree.

        :param tree: asdf file tree.
        :return: None
        """
        raise NotImplementedError()


def merge_strings(list_of_strings: Union[List[str], Tuple[str]]) -> dict:
    """
    Pack the list of strings into two arrays: the concatenated chars and the \
    individual string lengths. :func:`split_strings()` does the inverse.

    :param list_of_strings: The :class:`tuple` or :class:`list` of :class:`str`-s \
                            or :class:`bytes`-s to pack.
    :return: :class:`dict` with "strings" and "lengths" \
             :class:`numpy.ndarray`-s.
    """
    if not isinstance(list_of_strings, (tuple, list)):
        raise TypeError("list_of_strings must be either a tuple or a list")
    if len(list_of_strings) == 0:
        return {"strings": numpy.array([], dtype="S1"),
                "lengths": numpy.array([], dtype=int),
                "str": None}
    with_str = not isinstance(list_of_strings[0], bytes)
    if with_str:
        if not isinstance(list_of_strings[0], str):
            raise TypeError("list_of_strings must contain either bytes or strings")
        strings = numpy.array(["".join(list_of_strings).encode("utf-8")])
    else:
        merged = bytearray(sum(len(s) for s in list_of_strings))
        offset = 0
        for s in list_of_strings:
            merged[offset:offset + len(s)] = s
            offset += len(s)
        strings = numpy.frombuffer(merged, dtype="S%d" % len(merged))
    lengths = [0] * len(list_of_strings)
    for i, s in enumerate(list_of_strings):
        lengths[i] = len(s)
    lengths = squeeze_bits(numpy.array(lengths, dtype=int))
    return {"strings": strings, "lengths": lengths, "str": with_str}


def split_strings(subtree: dict) -> List[str]:
    """
    Produce the list of strings from the dictionary with concatenated chars \
    and lengths. Opposite to :func:`merge_strings()`.

    :param subtree: The dict with "strings" and "lengths".
    :return: :class:`list` of :class:`str`-s or :class:`bytes`.
    """
    strings = subtree["strings"]
    lengths = subtree["lengths"]
    if lengths.shape[0] == 0 and strings.shape[0] == 0:
        return []
    strings = strings[0]
    if subtree.get("str", True):
        strings = strings.decode("utf-8")
    result = [None] * lengths.shape[0]
    offset = 0
    for i, l in enumerate(lengths):
        result[i] = strings[offset:offset + l]
        offset += l
    return result


def disassemble_sparse_matrix(matrix: scipy.sparse.spmatrix) -> dict:
    """
    Transform a scipy.sparse matrix into the serializable collection of \
    :class:`numpy.ndarray`-s. :func:`assemble_sparse_matrix()` does the inverse.

    :param matrix: :mod:`scipy.sparse` matrix; csr, csc and coo formats are \
                   supported.
    :return: :class:`dict` with "shape", "format" and "data" - :class:`tuple` \
             of :class:`numpy.ndarray`.
    """
    fmt = matrix.getformat()
    if fmt not in ("csr", "csc", "coo"):
        raise ValueError("Unsupported scipy.sparse matrix format: %s." % fmt)
    result = {
        "shape": matrix.shape,
        "format": fmt
    }
    if isinstance(matrix, (scipy.sparse.csr_matrix, scipy.sparse.csc_matrix)):
        lengths = numpy.concatenate(([0], numpy.diff(matrix.indptr)))
        result["data"] = matrix.data, squeeze_bits(matrix.indices), squeeze_bits(lengths)
    elif isinstance(matrix, scipy.sparse.coo_matrix):
        result["data"] = matrix.data, (squeeze_bits(matrix.row), squeeze_bits(matrix.col))
    return result


def assemble_sparse_matrix(subtree: dict) -> scipy.sparse.spmatrix:
    """
    Transform a dictionary with "shape", "format" and "data" into the \
    :mod:`scipy.sparse` matrix. \
    Opposite to :func:`disassemble_sparse_matrix()`.

    :param subtree: :class:`dict` which describes the :mod:`scipy.sparse` \
                    matrix.
    :return: :mod:`scipy.sparse` matrix of the specified format.
    """
    matrix_class = getattr(scipy.sparse, "%s_matrix" % subtree["format"])
    if subtree["format"] in ("csr", "csc"):
        indptr = subtree["data"][2]
        if indptr[-1] != subtree["data"][0].shape[0]:
            # indptr is diff-ed
            subtree["data"][2] = indptr.cumsum()
    matrix = matrix_class(tuple(subtree["data"]), shape=subtree["shape"])
    return matrix


def squeeze_bits(arr: numpy.ndarray) -> numpy.ndarray:
    """Return a copy of an integer numpy array with the minimum bitness."""
    assert arr.dtype.kind in ("i", "u")
    if arr.dtype.kind == "i":
        assert arr.min() >= 0
    mlbl = int(arr.max()).bit_length()
    if mlbl <= 8:
        dtype = numpy.uint8
    elif mlbl <= 16:
        dtype = numpy.uint16
    elif mlbl <= 32:
        dtype = numpy.uint32
    else:
        dtype = numpy.uint64
    return arr.astype(dtype)
