import argparse
import logging
import unittest
import shutil
import os

from modelforge.tests import fake_dulwich as fake_git
from modelforge import backends as back
import modelforge.index as ind


class BackendTests(unittest.TestCase):
    cached_path = "/tmp/modelforge-test-cache"
    default_url = "https://github.com/src-d/models"
    default_index = {
        "models": {
            "docfreq": {
                "12345678-9abc-def0-1234-56789abcdef0": {
                    "url": "https://xxx",
                    "created_at": "13:00",
                    "code": "model_code %s",
                    "description": "model_description"},
                "1e3da42a-28b6-4b33-94a2-a5671f4102f4": {
                    "url": "https://xxx",
                    "created_at": "13:00",
                    "code": "%s",
                    "description": ""
                }}},
        "meta": {
            "docfreq": {
                "code": "readme_code %s",
                "description": "readme_description",
                "default": "12345678-9abc-def0-1234-56789abcdef0"}
        }}

    def clear(self):
        if os.path.exists(self.cached_path):
            shutil.rmtree(os.path.expanduser(self.cached_path))

    def setUp(self):
        ind.git = fake_git
        ind.Repo = fake_git.FakeRepo
        fake_git.FakeRepo.reset(self.default_index)

    def tearDown(self):
        self.clear()
        from dulwich.repo import Repo
        ind.Repo = Repo
        from dulwich import porcelain as git
        ind.git = git

    def test_register_backend(self):
        class Foo:
            pass

        with self.assertRaises(TypeError):
            back.register_backend(Foo)

        class Bar(back.StorageBackend):
            NAME = "Bar"

        back.register_backend(Bar)
        self.assertEqual(Bar, back.__registry__["Bar"])

    def test_create_backend_invalid_args(self):
        backup = back.config.BACKEND_ARGS
        back.config.BACKEND_ARGS = "lalala"
        with self.assertRaises(ValueError):
            back.create_backend("Bar")
        back.config.BACKEND_ARGS = backup
        backup = back.config.BACKEND_ARGS
        back.config.BACKEND_ARGS = ""

        class Bar(back.StorageBackend):
            NAME = "Bar"
        back.register_backend(Bar)
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        try:
            self.assertIsInstance(back.create_backend("Bar", git_index), Bar)
        finally:
            back.config.BACKEND_ARGS = backup

    def test_create_backend_noexc(self):
        backup = back.config.BACKEND_ARGS
        back.config.BACKEND_ARGS = "lalala"
        logger = logging.getLogger()
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        try:
            self.assertIsNone(back.create_backend_noexc(logger, name="Bar", git_index=git_index))
        finally:
            back.config.BACKEND_ARGS = backup

        self.assertIsNone(back.create_backend_noexc(logger, name="Bar!!!", git_index=git_index))

    def test_supply_backend(self):

        @back.supply_backend(optional=True)
        def test_optional(args, backend, log):
            return backend

        self.assertIsNone(test_optional(argparse.Namespace(
            index_repo=self.default_url, username="", password="", cache=self.cached_path,
            signoff=None, log_level="WARNING")))
        self.assertEqual(test_optional(self._get_args(index_repo=self.default_url)), 1)
        self.assertEqual(1, test_optional(self._get_args(index_repo="any_error_really")))

    def _get_args(self, index_repo):
        return argparse.Namespace(
            backend="none", args="", index_repo=index_repo, username="",
            password="", cache=self.cached_path, signoff=None, log_level="WARNING")


if __name__ == "__main__":
    unittest.main()
