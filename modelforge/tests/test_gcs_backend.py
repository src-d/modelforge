import io
from threading import Thread
import time
import unittest

from google.cloud.storage import Client

from modelforge.gcs_backend import GCSBackend
from modelforge.tests.modelforgecfg import BACKEND_ARGS

BUCKET = BACKEND_ARGS[len("bucket="):BACKEND_ARGS.find(",")]


@unittest.skip
class GCSBackendTests(unittest.TestCase):
    def setUp(self):
        self.back = GCSBackend(bucket=BUCKET)
        self.client = Client()
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

    def test_lock(self):
        boilerplate = "boilerplate"
        threads_numner = 2
        clients = [Client() for _ in range(threads_numner)]
        buckets = [c.get_bucket(BUCKET) for c in clients]
        backs = [GCSBackend(bucket=BUCKET) for _ in range(threads_numner)]

        def collide(index):
            back = backs[index]
            bucket = buckets[index]
            time.sleep(index / 10)
            with back.lock():
                blob = bucket.blob(boilerplate)
                if blob.exists():
                    contents = blob.download_as_string().decode()
                else:
                    contents = ""
                contents += "%d\n" % index
                blob.upload_from_string(contents)

        threads = [Thread(target=collide, args=(i,)) for i in range(threads_numner)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        blob = self.bucket.blob(boilerplate)
        self.assertTrue(blob.exists())
        try:
            numbers = {int(l) for l in blob.download_as_string().decode().split("\n") if l}
            self.assertEqual(numbers, set(range(threads_numner)))
        finally:
            blob.delete()

    def test_upload_model(self):
        pass

    def test_upload_index(self):
        pass


if __name__ == "__main__":
    unittest.main()
