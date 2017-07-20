import argparse
from datetime import datetime
import unittest
import uuid

from modelforge.meta import generate_meta, extract_index_meta


class MetaTests(unittest.TestCase):
    def test_generate_meta(self):
        fake = argparse.Namespace(meta="surprise")
        meta = generate_meta("first", (1, 0, 1), fake)
        self.assertIsInstance(meta, dict)
        self.assertEqual(meta["model"], "first")
        uuid.UUID(meta["uuid"])
        self.assertEqual(meta["dependencies"], ["surprise"])
        self.assertEqual(meta["version"], (1, 0, 1))
        self.assertIsInstance(meta["created_at"], datetime)

    def test_extract_index_meta(self):
        dt = datetime.now()
        meta = {
            "version": [1, 0, 2],
            "created_at": dt,
            "uuid": None,
            "dependencies": [{
                "version": [1, 0, 3],
                "created_at": dt,
                "uuid": "?",
                "dependencies": []
            }]
        }
        converted = extract_index_meta(meta, "https://xxx")
        self.assertIsInstance(converted, dict)
        self.assertEqual(converted["version"], [1, 0, 2])
        self.assertEqual(converted["created_at"], str(dt))
        self.assertEqual(converted["url"], "https://xxx")
        self.assertIsInstance(converted["dependencies"], list)
        self.assertEqual(len(converted["dependencies"]), 1)
        dep = converted["dependencies"][0]
        self.assertEqual(dep["version"], [1, 0, 3])
        self.assertEqual(dep["created_at"], str(dt))
        self.assertEqual(dep["uuid"], "?")
        self.assertEqual(dep["dependencies"], [])


if __name__ == "__main__":
    unittest.main()
