from typing import Union, BinaryIO

from modelforge.index import GitIndex


class StorageBackend:
    NAME = None

    def __init__(self, index: GitIndex=None, **kwargs):
        """
        A backend
        :param index: GitIndex where the index is maintained.
        """
        self._index = index

    @property
    def index(self) -> GitIndex:
        if self._index:
            return self._index
        raise AttributeError("No index was provided.")

    def reset(self, force: bool):
        """
        Initialize backend.
        :param force: If backend is not empty, force must be set to True.
        :return: None
        :raises BackendRequiredError: If supplied bucket is unusable.
        :raises ExistingBackendError: If backend is already initialized, and force set to False.
        """
        raise NotImplementedError

    def upload_model(self, path: str, meta: dict, force: bool) -> str:
        """
        Puts the given file to the remote storage.

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
        Downloads the model from the remote storage.

        :param source: URL to download.
        :param file: Path to the local file to write or open file object.
        :return: None
        :raises BackendRequiredError: If supplied bucket is unusable.
        :raises NonExistingModelError: If model does not exist.
        """
        raise NotImplementedError

    def delete_model(self, meta: dict):
        """
        Deletes the model associated to the metadata dictionary from the remote storage.

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
