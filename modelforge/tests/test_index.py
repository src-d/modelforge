import os
import shutil
import unittest
import modelforge.index as ind

from modelforge.tests import fake_dulwich as fake_git


class GitIndexTests(unittest.TestCase):
    cached_path = "/tmp/modelforge-test-cache"
    default_url = "https://github.com/src-d/models"
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
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

    def test_init_base(self):
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "https://github.com/src-d/models")
        self.assertEqual(git_index.repo, "src-d/models")
        self.assertEqual(git_index.cached_repo, "/tmp/modelforge-test-cache/src-d/models")
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/index.json"))
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq"))
        self.assertListEqual(sorted(os.listdir("/tmp/modelforge-test-cache/src-d/models/docfreq")),
                             ["12345678-9abc-def0-1234-56789abcdef0.md",
                              "1e3da42a-28b6-4b33-94a2-a5671f4102f4.md"])
        self.assertEqual(git_index.content, self.default_index)
        self.assertEqual(git_index.models, self.default_index["models"])
        self.assertEqual(git_index.meta, self.default_index["meta"])

    def test_init_fetch(self):
        ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        self.assertTrue(fake_git.FakeRepo.checkout)
        self.assertTrue(fake_git.FakeRepo.cloned)
        fake_git.FakeRepo.reset(self.default_index)
        ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        self.assertFalse(fake_git.FakeRepo.cloned)
        self.assertFalse(fake_git.FakeRepo.pulled)
        fake_git.FakeRepo.reset(self.default_index, head="1")
        ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        self.assertFalse(fake_git.FakeRepo.cloned)
        self.assertTrue(fake_git.FakeRepo.pulled)

    def test_init_errors(self):
        succeeded = True
        try:
            ind.GitIndex(index_repo="no_protocol", cache=self.cached_path)
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        try:
            ind.GitIndex(index_repo="badprotocol://github.com", cache=self.cached_path)
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        try:
            ind.GitIndex(index_repo="http:///nodomain", cache=self.cached_path)
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        try:
            ind.GitIndex(index_repo="http://nopath.com", cache=self.cached_path)
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        try:
            ind.GitIndex(index_repo="http://github.com/not-git-repo", cache=self.cached_path)
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        try:
            ind.GitIndex(index_repo="http://github.com/bad-ssh", cache=self.cached_path)
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        try:
            ind.GitIndex(index_repo="http://github.com/bad-credentials", cache=self.cached_path)
            succeeded = False
        except ValueError:
            self.assertTrue(succeeded)
        try:
            ind.GitIndex(index_repo=self.default_url, username="no-password",
                         cache=self.cached_path)
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        try:
            ind.GitIndex(index_repo=self.default_url, password="no-username",
                         cache=self.cached_path)
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)

    def test_init_variants(self):
        git_index = ind.GitIndex(
            index_repo="http://github.com/src-d/models", cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "http://github.com/src-d/models")
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        git_index = ind.GitIndex(
            index_repo="git://github.com/src-d/models", cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "git://github.com/src-d/models")
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        git_index = ind.GitIndex(
            index_repo="ssh://git@github.com/src-d/models", cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "ssh://git@github.com/src-d/models")
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        git_index = ind.GitIndex(
            index_repo="git+ssh://git@github.com/src-d/models", cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "git+ssh://git@github.com/src-d/models")
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        git_index = ind.GitIndex(
            index_repo=self.default_url, username="user", password="password",
            cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "https://user:password@github.com/src-d/models")
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        git_index = ind.GitIndex(
            index_repo="https://notgithub.com/src-d/models", cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "https://notgithub.com/src-d/models")
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        git_index = ind.GitIndex(
            index_repo="https://github.com/not/src-d/models", cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "https://github.com/not/src-d/models")
        self.assertEqual(git_index.repo, "not/src-d/models")
        self.assertEqual(git_index.cached_repo, "/tmp/modelforge-test-cache/not/src-d/models")
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        git_index = ind.GitIndex(
            index_repo="https://github.com/src-d.git/models.git", cache=self.cached_path)
        self.assertEqual(git_index.remote_url, "https://github.com/src-d.git/models.git")
        self.assertEqual(git_index.repo, "src-d.git/models")
        self.assertEqual(git_index.cached_repo, "/tmp/modelforge-test-cache/src-d.git/models")
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        cached_path = "/tmp/modelforge-test-cache/cache"
        git_index = ind.GitIndex(
            index_repo="https://github.com/src-d/models", cache=cached_path)
        self.assertEqual(git_index.repo, "src-d/models")
        self.assertEqual(git_index.cached_repo, "/tmp/modelforge-test-cache/cache/src-d/models")

    def test_remove(self):
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
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
        self.assertEqual(git_index.meta["docfreq"]["default"],
                         "12345678-9abc-def0-1234-56789abcdef0")
        self.assertFalse(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                        "1e3da42a-28b6-4b33-94a2-a5671f4102f4.md"))
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                       "12345678-9abc-def0-1234-56789abcdef0.md"))
        git_index.remove_model("12345678-9abc-def0-1234-56789abcdef0")
        self.assertNotIn("docfreq", git_index.models)
        self.assertNotIn("docfreq", git_index.meta)
        self.assertFalse(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"))
        self.clear()
        fake_git.FakeRepo.reset(self.default_index)
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        git_index.remove_model("12345678-9abc-def0-1234-56789abcdef0")
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                       "1e3da42a-28b6-4b33-94a2-a5671f4102f4.md"))
        self.assertFalse(os.path.exists("/tmp/modelforge-test-cache/src-d/models/docfreq/"
                                        "12345678-9abc-def0-1234-56789abcdef0.md"))
        self.assertIn("1e3da42a-28b6-4b33-94a2-a5671f4102f4", git_index.models["docfreq"])
        self.assertNotIn("12345678-9abc-def0-1234-56789abcdef0", git_index.models["docfreq"])
        self.assertEqual(git_index.meta["docfreq"]["default"], "")

    def test_add(self):
        template_path = os.path.join(self.templates_dir, "template_model.md.jinja2")
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        template = git_index.load_template(template_path)
        meta = {
            "default": {"default": "92609e70-f79c-46b5-8419-55726e873cfc",
                        "code": "readme_code %s", "description": "readme_description"},
            "model": {
                "code": "model_code %s",
                "description": "model_description",
                "size": "4 Bytes",
                "references": [["ref_name", "ref_url"]],
                "extra": {"ext": "data"},
                "license": ["license", "link"],
                "dependencies": [],
                "url": "http://xxx",
                "created_at": "13:42",
                "version": [1, 0, 3]
            }
        }
        git_index.add_model("docfreq", "92609e70-f79c-46b5-8419-55726e873cfc", meta, template)
        self.assertEqual(git_index.models["docfreq"]["92609e70-f79c-46b5-8419-55726e873cfc"],
                         meta["model"])
        self.assertNotEqual(git_index.meta["docfreq"]["default"],
                            "92609e70-f79c-46b5-8419-55726e873cfc")
        model_path = "/tmp/modelforge-test-cache/src-d/models/docfreq/" \
                     "92609e70-f79c-46b5-8419-55726e873cfc.md"
        self.assertTrue(os.path.exists(model_path))
        with open(model_path) as _in:
            model = _in.read()
        with open(os.path.join(os.path.dirname(__file__), "model.md")) as _in:
            real_model = _in.read()
        self.assertEqual(model, real_model)
        git_index.add_model("docfreq", "92609e70-f79c-46b5-8419-55726e873cfc", meta, template,
                            update_default=True)
        self.assertDictEqual(git_index.meta["docfreq"], meta["default"])
        git_index.add_model("other", "92609e70-f79c-46b5-8419-55726e873cfc", meta, template)
        self.assertEqual(git_index.models["other"]["92609e70-f79c-46b5-8419-55726e873cfc"],
                         meta["model"])
        self.assertDictEqual(git_index.meta["other"], meta["default"])
        self.assertTrue(os.path.exists("/tmp/modelforge-test-cache/src-d/models/other/"
                                       "92609e70-f79c-46b5-8419-55726e873cfc.md"))
        self.assertDictEqual(git_index.meta["other"], meta["default"])

    def test_readme(self):
        self.maxDiff = None
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        template_path = os.path.join(self.templates_dir, "template_readme.md.jinja2")
        template = git_index.load_template(template_path)
        git_index.update_readme(template)
        readme_path = "/tmp/modelforge-test-cache/src-d/models/README.md"
        self.assertTrue(os.path.exists(readme_path))
        with open(readme_path) as _in:
            readme = _in.read()
        with open(os.path.join(os.path.dirname(__file__), "readme.md")) as _in:
            real_readme = _in.read()
        self.assertEqual(readme, real_readme)

    def test_initialize(self):
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        with open(os.path.join(git_index.cached_repo, ".gitignore"), "w") as _out:
            _out.write("nothing")
        git_index.initialize_index()
        empty_index = {"models": {}, "meta": {}}
        self.assertDictEqual(empty_index, git_index.content)
        self.assertTrue(os.path.exists(git_index.cached_repo))
        self.assertListEqual(os.listdir(git_index.cached_repo), [".gitignore"])

    def test_upload_add(self):
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        git_index.upload_index("add", {"model": "a", "uuid": "b"})
        self.assertTrue(fake_git.FakeRepo.added)
        self.assertEqual(fake_git.FakeRepo.message, "Add a/b")
        self.assertTrue(fake_git.FakeRepo.pushed)

    def test_upload_delete(self):
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        git_index.upload_index("delete", {"model": "a", "uuid": "b"})
        self.assertTrue(fake_git.FakeRepo.added)
        self.assertEqual(fake_git.FakeRepo.message, "Delete a/b")
        self.assertTrue(fake_git.FakeRepo.pushed)

    def test_upload_init(self):
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        git_index.upload_index("initilialize", {})
        self.assertTrue(fake_git.FakeRepo.added)
        self.assertEqual(fake_git.FakeRepo.message, "Initialize a new Modelforge index")
        self.assertTrue(fake_git.FakeRepo.pushed)

    def test_upload_bug(self):
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        fake_git.FakeRepo.reset(self.default_index, head="1")
        succeeded = True
        try:
            git_index.upload_index("initilialize", {})
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)

    def test_template(self):
        git_index = ind.GitIndex(index_repo=self.default_url, cache=self.cached_path)
        succeeded = True
        try:
            git_index.load_template("fake.jinj4")
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        try:
            git_index.load_template("fake.jinja2")
            succeeded = False
        except ValueError:
            pass
        self.assertTrue(succeeded)
        template_path = os.path.join(self.templates_dir, "template_readme.md.jinja2")
        template = git_index.load_template(template_path)
        self.assertEqual(template.render(meta={}, models={}, links={}),
                         "source{d} MLonCode models\n=========================\n")


if __name__ == "__main__":
    unittest.main()
