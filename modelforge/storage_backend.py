class StorageBackend:
    NAME = None

    def __init__(self, **kwargs):
        pass

    def fetch_model(self, source: str, file: str) -> None:
        """
        Downloads the model from the remote storage.

        :param source: URL to download.
        :param file: PAth to the local file to write.
        :return: None
        """
        raise NotImplementedError

    def fetch_index(self) -> dict:
        """
        Downloads the index from the remote storage.

        :return: The current index.
        :raise FileNotFoundError: If there is not index - need to initialize.
        """
        raise NotImplementedError

    def lock(self):
        """
        Returns a scoped object which holds a lock.
        """
        raise NotImplementedError

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


class TransactionRequiredError(Exception):
    """
    User tried to change the index and did not acquire a lock.
    """
    pass
