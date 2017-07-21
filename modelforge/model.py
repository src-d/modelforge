import inspect
import logging
import os
import re
import shutil
import tempfile
import uuid
from pprint import pformat
from typing import Union

import asdf
import numpy
import scipy.sparse

import modelforge.configuration as config
from modelforge.storage_backend import StorageBackend

ARRAY_COMPRESSION = "zlib"


class Model:
    """
    Base class for all the models.
    """

    NAME = None  #: Name of the model. Used as the logging domain, too.
    VENDOR = None  #: The name of the issuing vendor, e.g. "source{d}"
    DEFAULT_NAME = "default"  #: When no uuid is specified, this is used.
    DEFAULT_FILE_EXT = ".asdf"  #: File extension of the model.

    def __init__(self, source: Union[str, "Model"]=None,
                 cache_dir: str=None, backend: StorageBackend=None,
                 log_level: int=logging.DEBUG):
        """
        Initializes a new Model instance.

        :param source: UUID, file system path or an URL; None means auto.
        :param cache_dir: The directory where to store the downloaded model.
        :param backend: Remote storage backend to use if ``source`` is a UUID or a URL.
        :param log_level: The logging level applied to this instance.
        """
        if isinstance(source, Model):
            if not isinstance(source, type(self)):
                raise TypeError("Incompatible model instance: %s <> %s" %
                                (type(source), type(self)))
            self.__dict__ = source.__dict__
            return

        if backend is not None and not isinstance(backend, StorageBackend):
            raise TypeError("backend must be an instance of "
                            "modelforge.storage_backend.StorageBackend")

        self._log = logging.getLogger(self.NAME)
        self._log.setLevel(log_level)
        self._source = source
        if cache_dir is None:
            if self.NAME is not None:
                cache_dir = os.path.join(self.cache_dir(), self.NAME)
            else:
                cache_dir = tempfile.mkdtemp(prefix="ast2vec-")
        try:
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
                index = backend.fetch_index()
                config = index["models"]
                if self.NAME is not None:
                    source = config[self.NAME][model_id]
                    if not is_uuid:
                        source = config[self.NAME][source]
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
            with asdf.open(source) as model:
                tree = model.tree
                self._meta = tree["meta"]
                if self.NAME != self._meta["model"] and self.NAME is not None:
                    raise ValueError(
                        "The supplied model is of the wrong type: needed "
                        "%s, got %s." % (self.NAME, self._meta["model"]))
                self.load(tree)
        finally:
            if self.NAME is None:
                shutil.rmtree(cache_dir)

    @property
    def meta(self):
        """
        Metadata dictionary: when was created, uuid, engine version, etc.
        """
        return self._meta

    def __str__(self):
        try:
            dump = self.dump()
        except NotImplementedError:
            dump = ""
        if dump:
            dump = "\n" + dump
        return "%s%s" % (pformat(self.meta), dump)

    def __repr__(self):
        module = inspect.getmodule(self)
        module_name = module.__name__
        if module_name == "__main__":
            if module.__spec__ is not None:
                module_name = module.__spec__.name
            else:
                module_name = "[%s]" % module.__file__
        return "%s.%s(source=%s)" % (module_name, type(self).__name__, self._source)

    def __getstate__(self):
        """
        Fixes pickling.
        """
        state = self.__dict__.copy()
        state["_log"] = self._log.level
        return state

    def __setstate__(self, state):
        log_level = state["_log"]
        self.__dict__.update(state)
        self._log = logging.getLogger(self.NAME)
        self._log.setLevel(log_level)

    @staticmethod
    def cache_dir():
        return os.path.join("~", "." + config.VENDOR)

    def get_dependency(self, name):
        deps = self.meta["dependencies"]
        for d in deps:
            if d["model"] == name:
                return d
        raise KeyError("%s not found in %s." % (name, deps))

    def load(self, tree: dict) -> None:
        """
        Attaches the needed data from the tree.

        :param tree: asdf file tree.
        :return: None
        """
        raise NotImplementedError()

    def dump(self) -> str:
        """
        Returns the string with the brief information about the model.
        Should not include any metadata.
        """
        raise NotImplementedError()


def merge_strings(list_of_strings):
    """
    Packs the list of strings into two arrays: the concatenated chars and the
    individual string lengths. :func:`split_strings()` does the inverse.

    :param list_of_strings: The :class:`list` of :class:`str`-s to pack.
    :return: :class:`dict` with "strings" and "lengths" \
             :class:`numpy.ndarray`-s.
    """
    strings = numpy.array(["".join(list_of_strings).encode("utf-8")])
    max_len = 0
    lengths = []
    for s in list_of_strings:
        l = len(s)
        lengths.append(l)
        if l > max_len:
            max_len = l
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
    return {"strings": strings, "lengths": lengths}


def split_strings(subtree):
    """
    Produces the list of strings from the dictionary with concatenated chars
    and lengths. Opposite to :func:`merge_strings()`.

    :param subtree: The dict with "strings" and "lengths".
    :return: :class:`list` of :class:`str`-s.
    """
    result = []
    strings = subtree["strings"][0].decode("utf-8")
    lengths = subtree["lengths"]
    offset = 0
    for i, l in enumerate(lengths):
        result.append(strings[offset:offset + l])
        offset += l
    return result


def disassemble_sparse_matrix(matrix):
    """
    Transforms a scipy.sparse matrix into the serializable collection of
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
        result["data"] = matrix.data, matrix.indices, matrix.indptr
    elif isinstance(matrix, scipy.sparse.coo_matrix):
        result["data"] = matrix.data, (matrix.row, matrix.col)
    return result


def assemble_sparse_matrix(subtree):
    """
    Transforms a dictionary with "shape", "format" and "data" into the
    :mod:`scipy.sparse` matrix.
    Opposite to :func:`disassemble_sparse_matrix()`.

    :param subtree: :class:`dict` which describes the :mod:`scipy.sparse` \
                    matrix.
    :return: :mod:`scipy.sparse` matrix of the specified format.
    """
    matrix_class = getattr(scipy.sparse, "%s_matrix" % subtree["format"])
    matrix = matrix_class(tuple(subtree["data"]), shape=subtree["shape"])
    return matrix


def write_model(meta: dict, tree: dict, output: str) -> None:
    """
    Writes the model to disk.

    :param meta: Metadata of the model. Most likely generated with \
                 :func:`modelforge.meta.generate_meta`.
    :param tree: The data dict.
    :param output: The output file path.
    :return: None
    """
    final_tree = {"meta": meta}
    final_tree.update(tree)
    asdf.AsdfFile(final_tree).write_to(output, all_array_compression=ARRAY_COMPRESSION)
