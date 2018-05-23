import argparse
import unittest

from modelforge.delete import delete_model
from modelforge.backends import StorageBackend, register_backend


@register_backend
class FakeBackend(StorageBackend):

    NAME = "del"
    index = {"models": {"docfreq": {"default": "2", "1": 1, "2": 2}}}
    model = [1, 2]

    def fetch_model(self, source: str, file: str) -> None:
        pass

    def fetch_index(self) -> dict:
        return self.index

    def upload_model(self, path: str, meta: dict, force: bool) -> str:
        pass

    def upload_index(self, index: dict) -> None:
        self.index = index

    def delete_model(self, meta: dict):
        if len(self.model):
            self.model.pop()

    def create_bucket(self):
        pass


class DeleteTests(unittest.TestCase):

    def test_delete(self):
        delete_model(argparse.Namespace(input="2", backend=FakeBackend.NAME, args=""))
        self.assertDictEqual(FakeBackend.index["models"], {"docfreq": {"1": 1}})
        self.assertListEqual(FakeBackend.model, [1])
        delete_model(argparse.Namespace(input="1", backend=FakeBackend.NAME, args=""))
        self.assertDictEqual(FakeBackend.index, {"models": {}})
        self.assertListEqual(FakeBackend.model, [])
        self.assertEqual(
            delete_model(argparse.Namespace(input="1", backend=FakeBackend.NAME, args="")), 1)
