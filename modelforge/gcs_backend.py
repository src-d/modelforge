import io
import logging
import os
from typing import BinaryIO, Union

from clint.textui import progress
from google.cloud.exceptions import NotFound

from modelforge.index import GitIndex
from modelforge.storage_backend import BackendRequiredError, DEFAULT_DOWNLOAD_CHUNK_SIZE, \
    download_http, ExistingBackendError, ModelAlreadyExistsError, StorageBackend


class GCSBackend(StorageBackend):
    """Google Cloud Storage backend. Each model file is a blob."""

    NAME = "gcs"

    class _Tracker:
        """
        Wrapper around a bytes buffer which follows the file position and updates \
        the console progressbar mimicking a file object.
        """

        def __init__(self, data: memoryview, logger: logging.Logger):
            self._file = io.BytesIO(data)
            self._size = len(data)
            self._enabled = logger.isEnabledFor(logging.INFO)
            if self._enabled:
                self._progress = progress.Bar(expected_size=self._size)
            else:
                logger.debug("Progress indication is not enabled")

        def read(self, size: int = None):
            pos_before = self._file.tell()
            result = self._file.read(size)
            if self._enabled:
                pos = self._file.tell()
                if pos != pos_before:
                    if pos < self._size:
                        self._progress.show(pos)
                    else:
                        self._progress.done()
            return result

        def __len__(self):
            return self._size

    def __init__(self, bucket: str, credentials: str="", index: GitIndex=None,
                 log_level: int=logging.DEBUG):
        """
        Initialize a new instance of :class:`GCSBackend`.

        :param bucket: The name of the Google Cloud Storage bucket to use.
        :param credentials: The path to the credentials for the Google Cloud Storage bucket.
        :param index: GitIndex where the index is maintained.
        :param log_level: The logging level of this instance.
        """
        super().__init__(index)
        if not isinstance(bucket, str):
            raise TypeError("bucket must be a str")
        self._bucket_name = bucket
        if not isinstance(credentials, str):
            raise TypeError("credentials must be a str")
        self._credentials = credentials
        self._log = logging.getLogger("gcs-backend")
        self._log.setLevel(log_level)

    @property
    def bucket_name(self) -> str:
        """Return the assigned bucket name."""
        return self._bucket_name

    @property
    def credentials(self) -> str:
        """
        Return the path to GCS credentials JSON file with all the needed config for \
        `from_service_account_json()`.
        """
        return self._credentials

    def create_client(self) -> "google.cloud.storage.Client":
        """
        Construct GCS API client.
        """
        # Client should be imported here because grpc starts threads during import
        # and if you call fork after that, a child process will be hang during exit
        from google.cloud.storage import Client
        if self.credentials:
            client = Client.from_service_account_json(self.credentials)
        else:
            client = Client()
        return client

    def connect(self) -> "google.cloud.storage.Bucket":
        """
        Connect to the assigned bucket.
        """
        log = self._log
        log.info("Connecting to the bucket...")
        client = self.create_client()
        return client.lookup_bucket(self.bucket_name)

    def reset(self, force):
        """Connect to the assigned bucket or create if needed. Clear all the blobs inside."""
        client = self.create_client()
        bucket = client.lookup_bucket(self.bucket_name)
        if bucket is not None:
            if not force:
                self._log.error("Bucket already exists, aborting.")
                raise ExistingBackendError
            self._log.info("Bucket already exists, deleting all content.")
            for blob in bucket.list_blobs():
                self._log.info("Deleting %s ..." % blob.name)
                bucket.delete_blob(blob.name)
        else:
            client.create_bucket(self.bucket_name)

    def upload_model(self, path: str, meta: dict, force: bool):
        """Put the model to GCS."""
        bucket = self.connect()
        if bucket is None:
            raise BackendRequiredError
        blob = bucket.blob("models/%s/%s.asdf" % (meta["model"], meta["uuid"]))
        if blob.exists() and not force:
            self._log.error("Model %s already exists, aborted.", meta["uuid"])
            raise ModelAlreadyExistsError
        self._log.info("Uploading %s from %s...", meta["model"], os.path.abspath(path))

        def tracker(data):
            return self._Tracker(data, self._log)

        make_transport = blob._make_transport

        def make_transport_with_progress(client):
            transport = make_transport(client)
            request = transport.request

            def request_with_progress(method, url, data=None, headers=None, **kwargs):
                return request(method, url, data=tracker(data), headers=headers, **kwargs)

            transport.request = request_with_progress
            return transport

        blob._make_transport = make_transport_with_progress

        with open(path, "rb") as fin:
            blob.upload_from_file(fin, content_type="application/x-yaml")
        blob.make_public()
        return blob.public_url

    def fetch_model(self, source: str, file: Union[str, BinaryIO],
                    chunk_size: int=DEFAULT_DOWNLOAD_CHUNK_SIZE) -> None:
        """Download the model from GCS."""
        download_http(source, file, self._log, chunk_size)

    def delete_model(self, meta: dict):
        """Delete the model from GCS."""
        bucket = self.connect()
        if bucket is None:
            raise BackendRequiredError
        blob_name = "models/%s/%s.asdf" % (meta["model"], meta["uuid"])
        self._log.info(blob_name)
        try:
            self._log.info("Deleting model ...")
            bucket.delete_blob(blob_name)
        except NotFound:
            self._log.warning("Model %s already deleted.", meta["uuid"])
