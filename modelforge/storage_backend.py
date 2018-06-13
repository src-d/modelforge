from modelforge.index import GitIndex


class StorageBackend:
    NAME = None

    def __init__(self, index: GitIndex=None, **kwargs):
        """
        A backend
        :param index: GitIndex where the index is maintained.
        """
        self._index = index

    def fetch_model(self, source: str, file: str) -> None:
        """
        Downloads the model from the remote storage.

        :param source: URL to download.
        :param file: PAth to the local file to write.
        :return: None
        """
        raise NotImplementedError

    @property
    def index(self) -> GitIndex:
        if self._index:
            return self._index
        raise AttributeError("No index was provided.")

    def upload_model(self, path: str, meta: dict, force: bool) -> str:
        """
        Puts the given file to the remote storage.

        :param path: Path to the model file.
        :param meta: Metadata of the model.
        :param force: Overwrite an existing model.
        :return: URL of the uploaded model.
        :raises TransactionRequiredError: If called not in a lock scope.
        """
        raise NotImplementedError

    def upload_index(self, index: dict) -> None:
        """
        Updates the index on the remote storage.

        :param index: The new index.
        :return: None
        :raises TransactionRequiredError: If called not in a lock scope.
        """
        raise NotImplementedError

    def delete_model(self, meta: dict):
        """
        Deletes the model associated to the metadata dictionary from the remote storage.

        :param meta: Metadata of the model.
        :raises TransactionRequiredError: If called not in a lock scope.
        """
        raise NotImplementedError


class TransactionRequiredError(Exception):
    """
    User tried to change the index and did not acquire a lock.
    """
    pass


class ModelExistsError(Exception):
    """
    User tried to publish a model that already exists without forcing.
    """
    pass
