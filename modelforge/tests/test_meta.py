from datetime import datetime
import os
import unittest
import uuid

import modelforge.meta as met
from modelforge.tests.fake_requests import FakeRequests


class MetaTests(unittest.TestCase):
    def test_generate_meta(self):
        meta = met.generate_new_meta("first", "new description", "MIT")
        self.assertIsInstance(meta, dict)
        self.assertEqual(meta["model"], "first")
        uuid.UUID(meta["uuid"])
        self.assertEqual(meta["dependencies"], [])
        self.assertEqual(meta["license"], "MIT")
        self.assertEqual(meta["version"], [1, 0, 0])
        self.assertEqual(meta["description"], "new description")
        self.assertIsInstance(meta["created_at"], datetime)
        self.assertIsNone(meta["parent"])
        self.assertIsNone(meta["series"])

        with self.assertRaises(ValueError):
            met.generate_new_meta("first", "new description", "Madrid")

    def test_extract_index_meta(self):
        self.maxDiff = None
        dt = datetime.now()
        base_meta = {
            "created_at": dt,
            "model": "docfreq",
            "series": "pga-2018",
            "uuid": "12345678-9abc-def0-1234-56789abcdef0",
            "version": [1, 0, 2],
            "parent": "f64bacd4-67fb-4c64-8382-399a8e7db52a",
            "dependencies": ["1e3da42a-28b6-4b33-94a2-a5671f4102f4"],
            "description": "model_description",
            "license": "MIT",
        }
        extra_meta = {
            "code": "model_code %s",
            "datasets": [["any", "https://any"]],
            "description": "override",
            "references": [["any", "ref"]]
        }

        def route(url):
            self.assertEqual("https://xxx", url)
            return b"content"

        met.requests = FakeRequests(route)
        model_meta = met.extract_model_meta(base_meta, extra_meta, "https://xxx")
        self.assertIsInstance(model_meta, dict)
        self.assertGreater(len(met.format_datetime(dt)), 0)
        self.assertDictEqual(
            model_meta, {
                "default": {"default": "12345678-9abc-def0-1234-56789abcdef0",
                            "description": "model_description"},
                "model": {"created_at": met.format_datetime(dt),
                          "code": "model_code %s",
                          "description": "model_description",
                          "dependencies": ["1e3da42a-28b6-4b33-94a2-a5671f4102f4"],
                          "license": "MIT",
                          "parent": "f64bacd4-67fb-4c64-8382-399a8e7db52a",
                          "datasets": [["any", "https://any"]],
                          "references": [["any", "ref"]],
                          "size": "7 Bytes",
                          "series": "pga-2018",
                          "source": "https://xxx",
                          "version": [1, 0, 2], }})


def get_path(name):
    return os.path.join(os.path.dirname(__file__), name)


if __name__ == "__main__":
    unittest.main()
