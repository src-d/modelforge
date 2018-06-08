import os
import json
import shutil
import unittest
import modelforge.index as ind

from modelforge.tests import fake_dulwich as fake_git
from modelforge.tests.fake_dulwich import FakeRepo
from modelforge.tests.fake_requests import FakeRequests


class GitIndexTests(unittest.TestCase):
    cached_path = "/tmp/modelforge-test-cache"
    default_repo = "src-d/models"

    def clear(self):
        if os.path.exists(self.cached_path):
            shutil.rmtree(os.path.expanduser(self.cached_path))

    def setUp(self):
        fake_git.FakeRepo.reset()
        ind.Repo = FakeRepo
        ind.git = fake_git

    def tearDown(self):
        self.clear()
        from dulwich.repo import Repo
        ind.Repo = Repo
        from dulwich import porcelain as git
        ind.git = git

    def test_init(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        self.assertTrue(FakeRepo.checkout)
        self.assertEqual(FakeRepo.remote_url, "https://github.com/src-d/models")
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/index.json"))
        self.assertEqual(git_index.index, FakeRepo.index)
        self.clear()
        FakeRepo.reset()
        ind.GitIndex(repo=self.default_repo, protocol="http", cache=self.cached_path)
        self.assertEqual(FakeRepo.remote_url, "http://github.com/src-d/models")
        self.clear()
        FakeRepo.reset()
        ind.GitIndex(repo=self.default_repo, protocol="ssh", cache=self.cached_path)
        self.assertEqual(FakeRepo.remote_url, "ssh://git@github.com/src-d/models")
        self.clear()
        FakeRepo.reset()
        ind.GitIndex(repo=self.default_repo, protocol="git+ssh", cache=self.cached_path)
        self.assertEqual(FakeRepo.remote_url, "git+ssh://git@github.com/src-d/models")
        self.clear()
        FakeRepo.reset()
        ind.GitIndex(repo=self.default_repo, username="user", password="password",
                     cache=self.cached_path)
        self.assertEqual(FakeRepo.remote_url, "https://user:password@github.com/src-d/models")
        self.clear()
        FakeRepo.reset()
        ind.GitIndex(repo=self.default_repo, domain="notgithub.com", cache=self.cached_path)
        self.assertEqual(FakeRepo.remote_url, "https://notgithub.com/src-d/models")
        self.clear()
        FakeRepo.reset()
        ind.GitIndex(repo="not/src-d/models", cache=self.cached_path)
        self.assertEqual(FakeRepo.remote_url, "https://github.com/not/src-d/models")
        self.clear()
        FakeRepo.reset()
        succeeded = True
        try:
            ind.GitIndex(repo="bad-url-1", cache=self.cached_path)
            succeeded = False
        except ValueError:
            self.assertTrue(succeeded)
        try:
            ind.GitIndex(repo="bad-url-2", cache=self.cached_path)
            succeeded = False
        except ValueError:
            self.assertTrue(succeeded)
        try:
            ind.GitIndex(repo="bad-url-3", cache=self.cached_path)
            succeeded = False
        except ValueError:
            self.assertTrue(succeeded)
        try:
            ind.GitIndex(repo=self.default_repo, username="no-password", cache=self.cached_path)
            succeeded = False
        except ValueError:
            self.assertTrue(succeeded)
        try:
            ind.GitIndex(repo=self.default_repo, password="no-username", cache=self.cached_path)
            succeeded = False
        except ValueError:
            self.assertTrue(succeeded)

    def test_fetch(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        git_index.fetch_index()
        self.assertFalse(FakeRepo.pulled)
        FakeRepo.remote_head = "1"
        git_index.fetch_index()
        self.assertTrue(FakeRepo.pulled)

    def test_remove(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        success = False
        try:
            git_index.remove_model("fake_uuid")
        except ValueError:
            success = True
        self.assertTrue(success)
        git_index.remove_model("1e3da42a-28b6-4b33-94a2-a5671f4102f4")
        self.assertNotIn("1e3da42a-28b6-4b33-94a2-a5671f4102f4",
                         git_index.models["docfreq"])
        self.assertIn("12345678-9abc-def0-1234-56789abcdef0", git_index.models["docfreq"])
        self.assertIn("default", git_index.models["docfreq"])
        self.assertFalse(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                        "1e3da42a-28b6-4b33-94a2-a5671f4102f4.md"))
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                       "12345678-9abc-def0-1234-56789abcdef0.md"))
        self.clear()
        FakeRepo.reset()
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        git_index.remove_model("12345678-9abc-def0-1234-56789abcdef0")
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                       "1e3da42a-28b6-4b33-94a2-a5671f4102f4.md"))
        self.assertFalse(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                        "12345678-9abc-def0-1234-56789abcdef0.md"))
        self.assertIn("1e3da42a-28b6-4b33-94a2-a5671f4102f4", git_index.models["docfreq"])
        self.assertNotIn("12345678-9abc-def0-1234-56789abcdef0", git_index.models["docfreq"])
        self.assertNotIn("default", git_index.models["docfreq"])
        git_index.remove_model("1e3da42a-28b6-4b33-94a2-a5671f4102f4")
        self.assertNotIn("docfreq", git_index.models)
        self.assertFalse(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"))

    def test_add(self):
        def router(url):
            return url

        ind.requests = FakeRequests(router)
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        base_meta = {"model": "docfreq", "uuid": "92609e70-f79c-46b5-8419-55726e873cfc",
                     "url": "https://xxx", "created_at": "13:00", "version": [1, 0, 0],
                     "dependencies": []}
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "templates/template_meta.json"), "r") as _in:
            extra_meta = json.load(_in)
        template = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "templates/template_model.md.jinja2")
        template_obj = git_index.load_template(template)
        git_index.add_model("docfreq", "92609e70-f79c-46b5-8419-55726e873cfc", base_meta,
                            extra_meta, "", template_obj)
        self.assertIn("92609e70-f79c-46b5-8419-55726e873cfc", git_index.index["models"]["docfreq"])
        self.assertNotEqual(git_index.index["models"]["docfreq"]["default"],
                            "92609e70-f79c-46b5-8419-55726e873cfc")
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                       "92609e70-f79c-46b5-8419-55726e873cfc.md"))
        git_index.add_model("docfreq", "92609e70-f79c-46b5-8419-55726e873cfc", base_meta,
                            extra_meta, "", template_obj, update_default=True)
        self.assertIn("92609e70-f79c-46b5-8419-55726e873cfc", git_index.index["models"]["docfreq"])
        self.assertEqual(git_index.index["models"]["docfreq"]["default"],
                         "92609e70-f79c-46b5-8419-55726e873cfc")
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                       "92609e70-f79c-46b5-8419-55726e873cfc.md"))
        base_meta.update({"model": "bow"})
        git_index.add_model("bow", "92609e70-f79c-46b5-8419-55726e873cfc", base_meta, extra_meta,
                            "test", template_obj)
        self.assertIn("92609e70-f79c-46b5-8419-55726e873cfc", git_index.index["models"]["bow"])
        self.assertEqual(git_index.index["models"]["bow"]["default"],
                         "92609e70-f79c-46b5-8419-55726e873cfc")
        model_path = "/tmp/modelforge-test-cache/src-d/models/bow/" \
                     "92609e70-f79c-46b5-8419-55726e873cfc.md"
        self.assertTrue(os.path.exists(model_path))
        with open(model_path) as _in:
            model = _in.read()
        with open(os.path.join(os.path.dirname(__file__), "model.md")) as _in:
            real_model = _in.read()
        self.assertEqual(model, real_model)
        import requests
        ind.requests = requests

    def test_readme(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        template = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "templates/template_readme.md.jinja2")
        template = git_index.load_template(template)
        git_index.update_readme(template)
        readme_path = "/tmp/modelforge-test-cache/src-d/models/README.md"
        self.assertTrue(os.path.exists(readme_path))
        with open(readme_path) as _in:
            readme = _in.read()
        with open(os.path.join(os.path.dirname(__file__), "readme.md")) as _in:
            real_readme = _in.read()
        self.assertEqual(readme, real_readme)

    def test_upload_init(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        fake_index = {"test": "test", "models": {}}
        git_index.index = fake_index
        git_index.models = {}
        git_index.upload_index("initilialize", {})
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/index.json"))
        git_index.fetch_index()
        self.assertEqual(fake_index, git_index.index)
        self.assertTrue(FakeRepo.added)
        self.assertEqual(FakeRepo.message, "Initialize a new Modelforge index")
        self.assertTrue(FakeRepo.pushed)

    def test_upload_add(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        fake_index = {"test": "test", "models": {}}
        git_index.index = fake_index
        git_index.models = {}
        git_index.upload_index("add", {"model_type": "a", "model_uuid": "b"})
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/index.json"))
        git_index.fetch_index()
        self.assertEqual(fake_index, git_index.index)
        self.assertTrue(FakeRepo.added)
        self.assertEqual(FakeRepo.message, "Add a/b")
        self.assertTrue(FakeRepo.pushed)

    def test_upload_delete(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        fake_index = {"test": "test", "models": {}}
        git_index.index = fake_index
        git_index.models = {}
        git_index.upload_index("delete", {"model_type": "a", "model_uuid": "b"})
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/index.json"))
        git_index.fetch_index()
        self.assertEqual(fake_index, git_index.index)
        self.assertTrue(FakeRepo.added)
        self.assertEqual(FakeRepo.message, "Delete a/b")
        self.assertTrue(FakeRepo.pushed)

    def test_template(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        succeeded = True
        try:
            git_index.load_template("fake.jinj4")
            succeeded = False
        except ValueError:
            self.assertTrue(succeeded)
        try:
            git_index.load_template("fake.jinja2")
            succeeded = False
        except ValueError:
            self.assertTrue(succeeded)
        template = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "templates/template_readme.md.jinja2")
        template_obj = git_index.load_template(template)
        self.assertEqual(template_obj.render({"models": {}}),
                         "source{d} MLonCode models\n=========================\n")

    def test_initialize_index(self):
        git_index = ind.GitIndex(repo=self.default_repo, cache=self.cached_path)
        git_index.initialize_index()
        self.assertEqual(git_index.index, {"models": {}})
        self.assertListEqual(os.listdir("/tmp/modelforge-test-cache/src-d/models/"), [])


if __name__ == "__main__":
    unittest.main()
