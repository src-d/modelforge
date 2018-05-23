import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
import os
import unittest

import modelforge.gcs_backend
from modelforge.backends import register_backend
from modelforge.registry import list_models, publish_model, initialize_registry
from modelforge.storage_backend import StorageBackend
from modelforge.tests.fake_requests import FakeRequests
from modelforge.tests.test_dump import captured_output


@register_backend
class FakeBackend(StorageBackend):
    NAME = "fake"
    uploaded_model = None
    uploaded_index = None
    default_index = {"models": {"docfreq": {
        "default": "12345678-9abc-def0-1234-56789abcdef0",
        "12345678-9abc-def0-1234-56789abcdef0": {
            "url": "https://xxx",
            "created_at": "13:00"
        }}}}
    index = deepcopy(default_index)

    def fetch_model(self, source: str, file: str) -> None:
        raise NotImplementedError

    def fetch_index(self) -> dict:
        return self.index

    def upload_model(self, path: str, meta: dict, force: bool) -> str:
        FakeBackend.uploaded_model = path, meta, force
        return "https:/yyy"

    def upload_index(self, index: dict) -> None:
        FakeBackend.uploaded_index = index

    @classmethod
    def reset(cls):
        cls.uploaded_model = None
        cls.uploaded_index = None
        cls.index = deepcopy(cls.default_index)

    def connect(self):
        pass


class RegistryTests(unittest.TestCase):
    def setUp(self):
        FakeBackend.reset()

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

    def test_publish(self):
        path = os.path.join(os.path.dirname(__file__), "test.asdf")
        args = argparse.Namespace(
            backend=FakeBackend.NAME, args=None, force=True, update_default=True, model=path)
        path = os.path.abspath(path)
        with captured_output() as (_, _, log):
            publish_model(args)
        self.assertEqual(log.getvalue(), """Reading %s...
Uploaded as https:/yyy
Updating the models index...
""" % path)
        self.assertEqual(FakeBackend.uploaded_model[0], path)
        self.assertEqual(FakeBackend.uploaded_model[1], {
            "created_at": datetime(2017, 6, 19, 9, 59, 14, 766638),
            "dependencies": [],
            "model": "docfreq",
            "uuid": "f64bacd4-67fb-4c64-8382-399a8e7db52a",
            "version": [1, 0, 0]})
        self.assertTrue(FakeBackend.uploaded_model[2])
        self.assertEqual(FakeBackend.uploaded_index, {
            "models": {"docfreq": {
                "default": "f64bacd4-67fb-4c64-8382-399a8e7db52a",
                "f64bacd4-67fb-4c64-8382-399a8e7db52a": {
                    "version": [1, 0, 0],
                    "dependencies": [],
                    "created_at": "2017-06-19 09:59:14.766638",
                    "url": "https:/yyy"},
                "12345678-9abc-def0-1234-56789abcdef0": {
                    "url": "https://xxx",
                    "created_at": "13:00"
                }
            }}
        })

    def test_publish_no_default_no_force(self):
        path = os.path.join(os.path.dirname(__file__), "test.asdf")
        args = argparse.Namespace(
            backend=FakeBackend.NAME, args=None, force=False, update_default=False, model=path)
        path = os.path.abspath(path)
        with captured_output() as (_, _, log):
            publish_model(args)
        self.assertEqual(log.getvalue(), """Reading %s...
Uploaded as https:/yyy
Updating the models index...
""" % path)
        self.assertEqual(FakeBackend.uploaded_model[0], path)
        self.assertEqual(FakeBackend.uploaded_model[1], {
            "created_at": datetime(2017, 6, 19, 9, 59, 14, 766638),
            "dependencies": [],
            "model": "docfreq",
            "uuid": "f64bacd4-67fb-4c64-8382-399a8e7db52a",
            "version": [1, 0, 0]})
        self.assertFalse(FakeBackend.uploaded_model[2])
        self.assertEqual(FakeBackend.uploaded_index, {
            "models": {"docfreq": {
                "default": "12345678-9abc-def0-1234-56789abcdef0",
                "f64bacd4-67fb-4c64-8382-399a8e7db52a": {
                    "version": [1, 0, 0],
                    "dependencies": [],
                    "created_at": "2017-06-19 09:59:14.766638",
                    "url": "https:/yyy"},
                "12345678-9abc-def0-1234-56789abcdef0": {
                    "url": "https://xxx",
                    "created_at": "13:00"
                }
            }}
        })

    def test_publish_fresh(self):
        path = os.path.join(os.path.dirname(__file__), "test.asdf")
        args = argparse.Namespace(
            backend=FakeBackend.NAME, args=None, force=True, update_default=True, model=path)
        FakeBackend.index = {"models": {}}
        with captured_output() as (_, _, log):
            publish_model(args)
        self.assertEqual(FakeBackend.uploaded_index, {
            "models": {"docfreq": {
                "default": "f64bacd4-67fb-4c64-8382-399a8e7db52a",
                "f64bacd4-67fb-4c64-8382-399a8e7db52a": {
                    "version": [1, 0, 0],
                    "dependencies": [],
                    "created_at": "2017-06-19 09:59:14.766638",
                    "url": "https:/yyy"}
            }}
        })

    def test_initialize(self):
        args = argparse.Namespace(backend=FakeBackend.NAME, args=None, force=True)
        with captured_output() as (_, _, log):
            initialize_registry(args)
        self.assertEqual(FakeBackend.uploaded_index, {"models": {}})

    def test_initialize_noforce(self):
        args = argparse.Namespace(backend=FakeBackend.NAME, args=None, force=False)
        with captured_output() as (_, _, log):
            initialize_registry(args)
        self.assertIsNone(FakeBackend.uploaded_index)


if __name__ == "__main__":
    unittest.main()
