import argparse
import os
import unittest

import modelforge.gcs_backend
from modelforge.registry import list_models, publish_model
from modelforge.tests.fake_requests import FakeRequests
from modelforge.tests.test_dump import captured_output


class RegistryTests(unittest.TestCase):
    def test_list(self):
        def route(url):
            return """
            {"models": {
                "xxx": {
                    "f64bacd4-67fb-4c64-8382-399a8e7db52a": {
                        "url": "https://xxx",
                        "created_at": "12:00"
                    },
                    "064bacd4-67fb-4c64-8382-399a8e7db52a": {
                        "url": "https://xxx2",
                        "created_at": "13:00"
                    },
                    "default": "f64bacd4-67fb-4c64-8382-399a8e7db52a"
                },
                "yyy": {
                    "f74bacd4-67fb-4c64-8382-399a8e7db52b": {
                        "url": "https://yyy",
                        "created_at": "11:00"
                    },
                    "f64bacd4-67fb-4c64-8382-399a8e7db52b": {
                        "url": "https://yyy",
                        "created_at": "12:00"
                    },
                    "default": "f64bacd4-67fb-4c64-8382-399a8e7db52b"
                },
                "zzz": {
                    "f64bacd4-67fb-4c64-8382-399a8e7db52c": {
                        "url": "https://zzz",
                        "created_at": "12:00"
                    },
                    "default": "f64bacd4-67fb-4c64-8382-399a8e7db52c"
                }
            }}""".encode()

        modelforge.gcs_backend.requests = FakeRequests(route)
        args = argparse.Namespace(backend=None, args=None)
        with captured_output() as (out, _, _):
            list_models(args)
        out = out.getvalue().split("\n")
        for name, uuids in (("xxx", ("064bacd4-67fb-4c64-8382-399a8e7db52a",
                                     "f64bacd4-67fb-4c64-8382-399a8e7db52a")),
                            ("yyy", ("f64bacd4-67fb-4c64-8382-399a8e7db52b",
                                     "f74bacd4-67fb-4c64-8382-399a8e7db52b")),
                            ("zzz", ("f64bacd4-67fb-4c64-8382-399a8e7db52c",))):
            idx = out.index(name)
            self.assertGreaterEqual(idx, 0)
            im = -1
            while idx < len(out):
                idx += 1
                im += 1
                if out[idx].startswith("  * "):
                    self.assertIn(uuids[im], out[idx])
                    break
                else:
                    self.assertEqual(out[idx][:4], "    ")
                    self.assertIn(uuids[im], out[idx])
            else:
                self.fail("The default model was not found.")

    @unittest.skip
    def test_publish(self):
        client = Client.from_service_account_json(self.CREDENTIALS)
        bucket = client.get_bucket(self.BUCKET)
        blob = bucket.get_blob(Id2Vec.INDEX_FILE)
        backup = blob.download_as_string()
        index = json.loads(backup.decode("utf-8"))
        del index["models"]["id2vec"]["92609e70-f79c-46b5-8419-55726e873cfc"]
        del index["models"]["id2vec"]["default"]
        updated = json.dumps(index, indent=4, sort_keys=True)
        blob.upload_from_string(updated)
        try:
            args = argparse.Namespace(
                model=os.path.join(os.path.dirname(__file__), paths.ID2VEC),
                gcs=self.BUCKET, update_default=True, force=False,
                credentials=self.CREDENTIALS)
            with captured_output() as (out, err, log):
                result = publish_model(args)
            self.assertEqual(result, 1)
            self.assertIn("Model 92609e70-f79c-46b5-8419-55726e873cfc already "
                          "exists, aborted", log.getvalue())
            blob = bucket.get_blob(
                "models/id2vec/92609e70-f79c-46b5-8419-55726e873cfc.asdf")
            bucket.rename_blob(
                blob,
                "models/id2vec/92609e70-f79c-46b5-8419-55726e873cfc.asdf.bak")
            try:
                with captured_output() as (out, err, log):
                    result = publish_model(args)
                blob = bucket.get_blob(
                    "models/id2vec/92609e70-f79c-46b5-8419-55726e873cfc.asdf")
                self.assertTrue(blob.exists())
                blob.delete()
                self.assertIsNone(result)
                self.assertIn("Uploaded as ", log.getvalue())
                self.assertIn("92609e70-f79c-46b5-8419-55726e873cfc", log.getvalue())
            finally:
                blob = bucket.get_blob(
                    "models/id2vec/92609e70-f79c-46b5-8419-55726e873cfc.asdf.bak")
                bucket.rename_blob(
                    blob, "models/id2vec/92609e70-f79c-46b5-8419-55726e873cfc.asdf")
                blob = bucket.get_blob(
                    "models/id2vec/92609e70-f79c-46b5-8419-55726e873cfc.asdf")
                blob.make_public()
            blob = bucket.get_blob(Id2Vec.INDEX_FILE)
            self.assertTrue(blob.download_as_string(), backup)
        finally:
            blob = bucket.get_blob(Id2Vec.INDEX_FILE)
            blob.upload_from_string(backup)
            blob.make_public()


if __name__ == "__main__":
    unittest.main()
