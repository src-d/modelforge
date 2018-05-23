import io
import unittest

from modelforge.gcs_backend import GCSBackend
from modelforge.tests.modelforgecfg import BACKEND_ARGS

BUCKET = BACKEND_ARGS[len("bucket="):BACKEND_ARGS.find(",")]


@unittest.skip
class GCSBackendTests(unittest.TestCase):
    def setUp(self):
        self.back = GCSBackend(bucket=BUCKET)
        self.bucket = self.client.get_bucket(BUCKET)

    def test_bucket_name(self):
        self.assertEqual(self.back.bucket_name, BUCKET)

    def test_credentials(self):
        self.assertFalse(self.back.credentials)

    def test_fetch_model(self):
        blob = self.bucket.blob("modelforge-test-fetch-model.bin")
        data = b"0123456789"
        blob.upload_from_string(data)
        blob.make_public()
        out = io.BytesIO()
        try:
            self.back.fetch_model(blob.public_url, out)
        finally:
            blob.delete()
        self.assertEqual(out.getvalue(), data)

    def test_fetch_index(self):
        blob = self.bucket.blob(GCSBackend.INDEX_FILE)
        if blob.exists():
            index_backup = blob.download_as_string()
        else:
            index_backup = ""
        blob.upload_from_string(b'{"models": {"test": 1234}}')
        blob.make_public()
        try:
            index = self.back.fetch_index()
            self.assertEqual(index["models"]["test"], 1234)
        finally:
            if index_backup:
                blob.upload_from_string(index_backup)
                blob.make_public()
            else:
                blob.delete()

    def test_connect(self):
        bucket = self.back.connect()
        self.assertEqual(bucket.path, BUCKET)
        bucket = GCSBackend(bucket="wrong_address").connect()
        self.assertIsNone(bucket)

    def test_upload_model(self):
        pass

    def test_upload_index(self):
        pass

    def test_delete_model(self):
        pass


if __name__ == "__main__":
    unittest.main()
