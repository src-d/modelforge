class StorageBackend:
    NAME = None

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
        """
        raise NotImplementedError

    def transaction(self):
        """
        Returns a scoped object which holds a transaction.
        """
        raise NotImplementedError

    def upload_model(self, path: str, meta: dict, force: bool) -> str:
        """
        Puts the given file to the remote storage.

        :param path: Path to the model file.
        :param meta: Metadata of the model.
        :param force: Overwrite an existing model.
        :return: URL of the uploaded model.
        :raises TransactionRequiredError: If called not in a transaction scope.
        """
        raise NotImplementedError

    def upload_index(self, index: dict) -> None:
        """
        Updates the index on the remote storage.

        :param index: The new index.
        :return: None
        :raises TransactionRequiredError: If called not in a transaction scope.
        """
        raise NotImplementedError


class TransactionRequiredError(Exception):
    pass
