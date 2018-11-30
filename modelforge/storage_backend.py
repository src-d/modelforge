import logging
import math
import os
from typing import BinaryIO, Union

import requests

from modelforge.index import GitIndex
from modelforge.progress_bar import progress_bar


class StorageBackend:
    """
    Abstract class to define the model storage backend interface.
    """

    NAME = None

    def __init__(self, index: GitIndex=None, **kwargs):
        """
        Initialize the backend.

        :param index: GitIndex where the index is maintained.
        """
        self._index = index

    @property
    def index(self) -> GitIndex:
        """
        Get the associated models index object.
        """
        if self._index:
            return self._index
        raise AttributeError("No index was provided.")

    def reset(self, force: bool):
        """
        Initialize the backend's state. This involves e.g. creating the directory structure, \
        creating DB tables, allocating a new blob storage entry on the web, etc.

        :param force: If backend is not empty, `force` must be set to True.
        :return: None
        :raises BackendRequiredError: If supplied bucket is unusable.
        :raises ExistingBackendError: If backend is already initialized, and `force` set to False.
        """
        raise NotImplementedError

    def upload_model(self, path: str, meta: dict, force: bool) -> str:
        """
        Put the given file to the remote storage.

        :param path: Path to the model file.
        :param meta: Metadata of the model.
        :param force: Overwrite an existing model.
        :return: URL of the uploaded model.
        :raises BackendRequiredError: If supplied bucket is unusable.
        :raises ModelAlreadyExistsError: If model already exists and no forcing.
        """
        raise NotImplementedError

    def fetch_model(self, source: str, file: Union[str, BinaryIO]) -> None:
        """
        Download the model from the remote storage.

        :param source: URL to download.
        :param file: Path to the local file to write or open file object.
        :return: None
        :raises BackendRequiredError: If supplied bucket is unusable.
        :raises NonExistingModelError: If model does not exist.
        """
        raise NotImplementedError

    def delete_model(self, meta: dict):
        """
        Delete the model associated to the metadata dictionary from the remote storage.

        :param meta: Metadata of the model.
        :raises BackendRequiredError: If supplied bucket is unusable.
        :raises NonExistingModelError: If model does not exist.
        """
        raise NotImplementedError


class ExistingBackendError(Exception):
    """
    User tried to initialize a backend that already was initialized without forcing.
    """

    pass


class BackendRequiredError(Exception):
    """
    User tried to publish or delete a model, but the supplied bucket parameters were incorrect.
    """

    pass


class ModelAlreadyExistsError(Exception):
    """
    User tried to publish a model that already exists without forcing.
    """

    pass


DEFAULT_DOWNLOAD_CHUNK_SIZE = 65536


def download_http(source: str, file: Union[str, BinaryIO], log: logging.Logger,
                  chunk_size: int=DEFAULT_DOWNLOAD_CHUNK_SIZE) -> None:
    """
    Download a file from an HTTP source.

    :param source: URL to fetch.
    :param file: Where to store the downloaded data.
    :param log: Logger.
    :param chunk_size: Size of download buffer.
    """
    log.info("Fetching %s...", source)
    r = requests.get(source, stream=True)
    if r.status_code != 200:
        log.error(
            "An error occurred while fetching the model, with code %s" % r.status_code)
        raise ValueError
    if isinstance(file, str):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        f = open(file, "wb")
    else:
        f = file
    try:
        total_length = int(r.headers.get("content-length"))
        num_chunks = math.ceil(total_length / chunk_size)
        if num_chunks == 1:
            f.write(r.content)
        else:
            for chunk in progress_bar(
                    r.iter_content(chunk_size=chunk_size),
                    log,
                    expected_size=num_chunks):
                if chunk:
                    f.write(chunk)
    finally:
        if isinstance(file, str):
            f.close()
