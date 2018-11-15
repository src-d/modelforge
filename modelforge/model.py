import inspect
import logging
import os
from pprint import pformat
import re
import shutil
import tempfile
from typing import BinaryIO, Iterable, List, Tuple, Union
import uuid

import asdf
import numpy
import pygtrie
import scipy.sparse

import modelforge.configuration as config
from modelforge.meta import generate_meta
from modelforge.storage_backend import StorageBackend


class Model:
    """
    Base class for all the models. All models should be backwards compatible: \
    base class should be able to load the file generated from an inheritor.
    """

    NAME = None  #: Name of the model. Used as the logging domain, too.
    VENDOR = None  #: The name of the issuing vendor, e.g. "source{d}"
    DEFAULT_NAME = "default"  #: When no uuid is specified, this is used.
    DEFAULT_FILE_EXT = ".asdf"  #: File extension of the model.
    NO_COMPRESSION = tuple()  #: Tree path prefixes which should not be compressed.
    # Note: "/" is automatically appended to all the compared paths.
    # Paths always start with a "/".
    ARRAY_COMPRESSION = "lz4"  #: ASDF default compression, options: zlib, bzp2, lz4

    def __init__(self, **kwargs):
        """
        Initialize a new Model instance.

        :param kwargs: Everything is ignored except ``log_level``.
        """
        self._log = logging.getLogger(self.NAME)
        self._log.setLevel(kwargs.get("log_level", logging.DEBUG))
        self._source = None
        self._meta = generate_meta(self.NAME, (1, 0, 0))
        self._meta["__init__"] = True
        self._asdf = None
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
        try:
            if source is None or (isinstance(source, str) and not os.path.isfile(source)):
                if cache_dir is None:
                    if self.NAME is not None:
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
                    if self.NAME is not None:
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
                    source = file_name
            self._log.info("Reading %s...", source)
            model = asdf.open(source, copy_arrays=not lazy, lazy_load=lazy)
            try:
                tree = model.tree
                self._meta = tree["meta"]
                if self.NAME is not None:
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
            if self.NAME is None and cache_dir is not None:
                shutil.rmtree(cache_dir)
        return self

    @property
    def meta(self):
        """
        Metadata dictionary: when was created, uuid, version, etc.
        """
        return self._meta

    def metaprop(name):
        """Temporary property builder."""
        def get(self):
            return self.meta[name]

        def set(self, value):
            self.meta[name] = value

        return property(get, set)

    uuid = metaprop("uuid")
    description = metaprop("description")
    references = metaprop("references")
    extra = metaprop("extra")
    created_at = metaprop("created_at")
    version = metaprop("version")
    parent = metaprop("parent")
    license = metaprop("license")

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
        if new_version is None:
            new_version = meta["version"]
            if not meta.get("__init__", False):
                new_version[-1] += 1
        if not isinstance(new_version, (tuple, list)):
            raise ValueError("new_version must be either a list or a tuple, got %s"
                             % type(new_version))
        meta["version"] = list(new_version)
        if not meta.get("__init__", False):
            meta["parent"] = meta["uuid"]
            meta["uuid"] = str(uuid.uuid4())
        else:
            del meta["__init__"]
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
        return "%s%s" % (pformat(self.meta), dump)

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
        state = self.__dict__.copy()
        state["_log"] = self._log.level
        return state

    def __setstate__(self, state):
        """
        Fix unpickling.
        """
        log_level = state["_log"]
        self.__dict__.update(state)
        self._log = logging.getLogger(self.NAME)
        self._log.setLevel(log_level)

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

    def save(self, output: Union[str, BinaryIO], deps: Iterable=tuple(),
             create_missing_dirs: bool=True) -> "Model":
        """
        Serialize the model to a file.

        :param output: path to the file or a file object.
        :param deps: the list of the dependencies.
        :param create_missing_dirs: create missing directories in output path if the output is a \
                                    path.
        :return: self
        """
        assert self.NAME is not None
        if isinstance(output, str) and create_missing_dirs:
            dirs = os.path.split(output)[0]
            if dirs:
                os.makedirs(dirs, exist_ok=True)
        self.set_dep(*deps).derive()
        tree = self._generate_tree()
        self._write_tree(tree, output)
        return self

    def _write_tree(self, tree: dict, output: Union[str, BinaryIO], file_mode: int=0o666) -> None:
        """
        Write the model to disk.

        :param tree: The data dict - will be the ASDF tree.
        :param output: The output file path or a file object.
        :param file_mode: The output file's permissions.
        :return: None
        """
        meta = self.meta.copy()
        meta.pop("__init__", None)
        final_tree = {"meta": meta}
        final_tree.update(tree)
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
        if isinstance(output, str):
            os.chmod(output, file_mode)

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
    max_len = 0
    lengths = [0] * len(list_of_strings)
    for i, s in enumerate(list_of_strings):
        length = len(s)
        lengths[i] = length
        if length > max_len:
            max_len = length
    bl = max_len.bit_length()
    if bl <= 8:
        dtype = numpy.uint8
    elif bl <= 16:
        dtype = numpy.uint16
    elif bl <= 32:
        dtype = numpy.uint32
    else:
        raise ValueError("There are very long strings (max length %d)."
                         % max_len)
    lengths = numpy.array(lengths, dtype=dtype)
    return {"strings": strings, "lengths": lengths, "str": with_str}


def split_strings(subtree: dict) -> List[str]:
    """
    Produce the list of strings from the dictionary with concatenated chars \
    and lengths. Opposite to :func:`merge_strings()`.

    :param subtree: The dict with "strings" and "lengths".
    :return: :class:`list` of :class:`str`-s or :class:`bytes`.
    """
    strings = subtree["strings"][0]
    if subtree.get("str", True):
        strings = strings.decode("utf-8")
    lengths = subtree["lengths"]
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
        mlbl = int(lengths.max()).bit_length()
        if mlbl <= 8:
            dtype = numpy.uint8
        elif mlbl <= 16:
            dtype = numpy.uint16
        elif mlbl <= 32:
            dtype = numpy.uint32
        else:
            dtype = numpy.uint64
        lengths = lengths.astype(dtype)
        result["data"] = matrix.data, matrix.indices, lengths
    elif isinstance(matrix, scipy.sparse.coo_matrix):
        result["data"] = matrix.data, (matrix.row, matrix.col)
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
