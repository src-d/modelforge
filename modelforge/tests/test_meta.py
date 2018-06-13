import argparse
from datetime import datetime
import unittest
import uuid
import os

import modelforge.meta as met
from modelforge.tests.fake_requests import FakeRequests


class MetaTests(unittest.TestCase):
    def test_generate_meta(self):
        fake = argparse.Namespace(meta="surprise")
        meta = met.generate_meta("first", (1, 0, 1), fake)
        self.assertIsInstance(meta, dict)
        self.assertEqual(meta["model"], "first")
        uuid.UUID(meta["uuid"])
        self.assertEqual(meta["dependencies"], ["surprise"])
        self.assertEqual(meta["version"], (1, 0, 1))
        self.assertIsInstance(meta["created_at"], datetime)

    def test_generate_meta_deps(self):
        fake = {"surprise": "me"}
        meta = met.generate_meta("first", (1, 0, 1), fake)
        self.assertIsInstance(meta, dict)
        self.assertEqual(meta["model"], "first")
        uuid.UUID(meta["uuid"])
        self.assertEqual(meta["dependencies"], [{"surprise": "me"}])
        self.assertEqual(meta["version"], (1, 0, 1))
        self.assertIsInstance(meta["created_at"], datetime)

    def test_extract_index_meta(self):
        self.maxDiff = None
        dt = str(datetime.now())
        base_meta = {
            "created_at": dt,
            "model": "docfreq",
            "uuid": "12345678-9abc-def0-1234-56789abcdef0",
            "version": [1, 0, 2]}
        extra_meta = {
            "code": "readme_code %s",
            "description": "readme_description",
            "model": {
                "code": "model_code %s",
                "description": "model_description",
                "dependencies": ["1e3da42a-28b6-4b33-94a2-a5671f4102f4"],
                "extra": {"ex": "tra"},
                "license": ["", "undecided"],
                "parent": "f64bacd4-67fb-4c64-8382-399a8e7db52a",
                "references": [["any", "ref"]]
            }}

        def route(url):
            self.assertEqual("https://xxx", url)
            return b"content"

        met.requests = FakeRequests(route)
        model_meta = met.extract_model_meta(base_meta, extra_meta, "https://xxx")
        self.assertIsInstance(model_meta, dict)
        self.assertDictEqual(
            model_meta, {"code": "model_code %s",
                         "created_at": dt,
                         "default": {"code": "readme_code %s",
                                     "default": "12345678-9abc-def0-1234-56789abcdef0",
                                     "description": "readme_description"},
                         "dependencies": ["1e3da42a-28b6-4b33-94a2-a5671f4102f4"],
                         "description": "model_description",
                         "extra": {"ex": "tra"},
                         "license": ["", "undecided"],
                         "parent": "f64bacd4-67fb-4c64-8382-399a8e7db52a",
                         "references": [["any", "ref"]],
                         "size": "7 Bytes",
                         "url": "https://xxx",
                         "version": [1, 0, 2]})


def get_path(name):
    return os.path.join(os.path.dirname(__file__), name)


if __name__ == "__main__":
    unittest.main()
