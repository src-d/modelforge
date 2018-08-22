import datetime
import inspect
import os
import pickle
import tempfile
import unittest
import shutil
import asdf
import numpy
from io import BytesIO
from scipy.sparse import csr_matrix

import modelforge.gcs_backend as back
import modelforge.index as ind
import modelforge.tests.fake_dulwich as fake_git

from modelforge import configuration
from modelforge.meta import generate_meta
from modelforge.backends import create_backend
from modelforge.model import merge_strings, split_strings, assemble_sparse_matrix, \
    disassemble_sparse_matrix, Model
from modelforge.models import GenericModel, register_model
from modelforge.tests.fake_requests import FakeRequests


@register_model
class FakeDocfreqModel(Model):

    NAME = "docfreq"

    def _load_tree(self, tree):
        self.docs = tree["docs"]

    def dump(self):
        return str(self.docs)

    def _generate_tree(self) -> dict:
        pass


class Model1(Model):
    def _load_tree(self, tree):
        pass

    def dump(self):
        return "model1"


class Model2(Model):
    NAME = "model2"

    def _load_tree(self, tree):
        pass

    def dump(self):
        return "model2"


class Model3(Model):
    def _load_tree(self, tree):
        pass


class Model4(Model):
    def dump(self):
        return str(self.xxx)


class Model5(Model):
    NAME = "aux"

    def _load_tree(self, tree):
        pass


class Model6(Model5):
    NAME = "docfreq"

    def _load_tree(self, tree):
        pass


class Model7(Model6):
    NAME = "xxx"

    def _load_tree(self, tree):
        pass


class Model8(Model):
    NAME = "model8"

    def _load_tree(self, tree):
        self.tree = tree

    def _generate_tree(self):
        return {"abc": 777}

    def dump(self):
        return "model8"


class FakeIndex:
    def __init__(self, index):
        self.index = index


def get_path(name):
    return os.path.join(os.path.dirname(__file__), name)


class ModelTests(unittest.TestCase):
    DOCFREQ_PATH = "test.asdf"
    cached_path = "/tmp/modelforge-test-cache"
    default_url = "https://github.com/src-d/models"
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    default_index = {
        "models": {
            "docfreq": {
                "f64bacd4-67fb-4c64-8382-399a8e7db52a": {
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
                "default": "f64bacd4-67fb-4c64-8382-399a8e7db52a"}}}

    def setUp(self):
        ind.git = fake_git
        ind.Repo = fake_git.FakeRepo
        fake_git.FakeRepo.reset(self.default_index)
        self.backend = create_backend(
            git_index=ind.GitIndex(index_repo=self.default_url, cache=self.cached_path))

    def clear(self):
        if os.path.exists(self.cached_path):
            shutil.rmtree(os.path.expanduser(self.cached_path))

    def tearDown(self):
        self.clear()
        from dulwich.repo import Repo
        ind.Repo = Repo
        from dulwich import porcelain as git
        ind.git = git

    def test_file(self):
        model = GenericModel(source=get_path(self.DOCFREQ_PATH))
        self._validate_meta(model)
        vendor = configuration.VENDOR
        configuration.VENDOR = None
        try:
            model = GenericModel(source=get_path(self.DOCFREQ_PATH))
            self._validate_meta(model)
        finally:
            configuration.VENDOR = vendor

    def test_error(self):
        with self.assertRaises(ValueError):
            GenericModel(source="f64bacd4-67fb-4c64-8382-399a8e7db52a")

    def test_id(self):
        def route(url):
            self.assertEqual("https://xxx", url)
            with open(get_path(self.DOCFREQ_PATH), "rb") as fin:
                return fin.read()

        back.requests = FakeRequests(route)
        model = GenericModel(
            source="f64bacd4-67fb-4c64-8382-399a8e7db52a", backend=self.backend)
        self._validate_meta(model)

    def test_url(self):
        def route(url):
            self.assertEqual("https://xxx", url)
            with open(get_path(self.DOCFREQ_PATH), "rb") as fin:
                return fin.read()

        back.requests = FakeRequests(route)
        model = GenericModel(source="https://xxx", backend=self.backend)
        self._validate_meta(model)

    def test_auto(self):
        class FakeModel(GenericModel):
            NAME = "docfreq"

        def route(url):
            self.assertEqual("https://xxx", url)
            with open(get_path(self.DOCFREQ_PATH), "rb") as fin:
                return fin.read()

        back.requests = FakeRequests(route)
        model = FakeModel(backend=self.backend)
        self._validate_meta(model)

    def test_bad_code(self):
        def route(url):
            self.assertEqual("https://bad_code", url)
            return 404

        back.requests = FakeRequests(route)
        with self.assertRaises(ValueError):
            GenericModel(source="https://bad_code", backend=self.backend)

    def test_init_with_model(self):
        model1 = Model1().load(source=get_path(self.DOCFREQ_PATH))
        # init with correct model
        Model1(source=model1)
        # init with wrong model
        with self.assertRaises(TypeError):
            Model2().load(source=model1)

    def test_repr_str(self):
        self.maxDiff = None
        path = get_path(self.DOCFREQ_PATH)
        model = Model1().load(source=path)
        repr1 = repr(model)
        try:
            self.assertIn("test_model.py].Model1().load(source=\"%s\")" % path, repr1)
        except AssertionError:
            self.assertEqual("modelforge.tests.test_model.Model1().load(source=\"%s\")"
                             % path, repr1)
        str1 = str(model)
        self.assertEqual(len(str1.split("\n")), 6)
        self.assertIn("\nmodel1", str1)
        self.assertIn("'uuid': 'f64bacd4-67fb-4c64-8382-399a8e7db52a'", str1)
        model = Model3().load(source=path)
        str2 = str(model)
        self.assertEqual(len(str2.split("\n")), 5)
        model = FakeDocfreqModel().load(source=path)
        repr2 = repr(model)
        self.assertEqual("[%s].FakeDocfreqModel().load(source=\"%s\")"
                         % (os.path.realpath(__file__), path), repr2)

    def test_repr_main(self):
        path = get_path(self.DOCFREQ_PATH)
        model = Model1().load(source=path)
        module = inspect.getmodule(model)
        module.__name__ = "__main__"
        module.__spec__ = None
        module_file = module.__file__
        del module.__file__
        try:
            repr2 = repr(model)
        finally:
            module.__file__ = module_file
        self.assertEqual("[unknown].Model1().load(source=\"%s\")" % path, repr2)

    def test_get_dep(self):
        model = Model1().load(source=get_path(self.DOCFREQ_PATH))
        model.meta["dependencies"] = [{"model": "xxx", "uuid": "yyy"},
                                      {"model": "zzz", "uuid": None}]
        self.assertEqual(model.get_dep("xxx")["uuid"], "yyy")

    def _validate_meta(self, model):
        meta = model.meta
        self.assertIsInstance(meta, dict)
        self.assertEqual(meta, {
            'created_at': datetime.datetime(2017, 6, 19, 9, 59, 14, 766638),
            'dependencies': [],
            'model': 'docfreq',
            'uuid': 'f64bacd4-67fb-4c64-8382-399a8e7db52a',
            'version': [1, 0, 0]})

    def test_uninitialized_dump(self):
        text = str(Model4())
        try:
            self.assertIn("test_model.py].Model4().load(source=None)", text)
        except AssertionError:
            self.assertEqual("modelforge.tests.test_model.Model4().load(source=None)", text)

    def test_name_check(self):
        Model5().load(source=get_path(self.DOCFREQ_PATH))
        Model6().load(source=get_path(self.DOCFREQ_PATH))
        with self.assertRaises(ValueError):
            Model7().load(source=get_path(self.DOCFREQ_PATH))

    def test_derive(self):
        path = get_path(self.DOCFREQ_PATH)
        model = Model1().load(source=path)
        m2 = model.derive()
        self.assertEqual(m2.version, [1, 0, 1])
        model.derive((2, 0, 0))
        self.assertEqual(m2.version, [2, 0, 0])
        with self.assertRaises(ValueError):
            model.derive("1.2.3")

    def test_derive_init(self):
        model = Model1()
        self.assertTrue(model.meta["__init__"])
        model.derive()
        self.assertEqual(model.version, [1, 0, 0])

    def test_set_dep(self):
        model1 = Model1()
        model2 = Model2()
        model1.set_dep(model2)
        self.assertIs(model1.get_dep("model2"), model2.meta)

    def test_props(self):
        path = get_path(self.DOCFREQ_PATH)
        model = Model1().load(source=path)
        for n in ("description", "references", "extra", "parent", "license"):
            with self.assertRaises(KeyError):
                getattr(model, n)
        self.assertEqual(model.version, [1, 0, 0])
        self.assertEqual(model.created_at, datetime.datetime(2017, 6, 19, 9, 59, 14, 766638))

    def test_init_version(self):
        self.assertEqual(Model1().version, [1, 0, 0])

    def test_save(self):
        with tempfile.NamedTemporaryFile(prefix="modelforge-test-") as f:
            Model8().save(f.name)
            self.assertEqual(Model8().load(f.name).tree["abc"], 777)

    def test_save_no_name(self):
        with self.assertRaises(AssertionError):
            Model4().save("model.asdf")

    def test_save_create_missing_dirs(self):
        with tempfile.TemporaryDirectory(prefix="modelforge-test-") as savedir:
            savepath = os.path.join(savedir, "add/some/subdirs/", "model.asdf")
            with self.assertRaises(FileNotFoundError):
                Model8().save(savepath, create_missing_dirs=False)
            Model8().save(savepath)
            self.assertEqual(Model8().load(savepath).tree["abc"], 777)


class SerializationTests(unittest.TestCase):
    DOCFREQ_PATH = "test.asdf"

    def test_merge_strings(self):
        strings = ["a", "bc", "def"]
        merged = merge_strings(strings)
        self.assertIsInstance(merged, dict)
        self.assertIn("strings", merged)
        self.assertIn("lengths", merged)
        self.assertIsInstance(merged["strings"], numpy.ndarray)
        self.assertEqual(merged["strings"].shape, (1,))
        self.assertEqual(merged["strings"][0], b"abcdef")
        self.assertIsInstance(merged["lengths"], numpy.ndarray)
        self.assertEqual(merged["lengths"].shape, (3,))
        self.assertEqual(merged["lengths"][0], 1)
        self.assertEqual(merged["lengths"][1], 2)
        self.assertEqual(merged["lengths"][2], 3)

    def test_split_strings(self):
        strings = split_strings({
            "strings": numpy.array([b"abcdef"]),
            "lengths": numpy.array([1, 2, 3])
        })
        self.assertEqual(strings, ["a", "bc", "def"])

    def test_invalid_merge_strings(self):
        with self.assertRaises(TypeError):
            merge_strings("abcd")
        with self.assertRaises(TypeError):
            merge_strings([0, 1, 2, 3])

    def test_merge_bytes(self):
        strings = [b"a", b"bc", b"def"]
        merged = merge_strings(strings)
        self.assertIsInstance(merged, dict)
        self.assertIn("strings", merged)
        self.assertIn("lengths", merged)
        self.assertEqual(merged["str"], False)
        self.assertIsInstance(merged["strings"], numpy.ndarray)
        self.assertEqual(merged["strings"].shape, (1,))
        self.assertEqual(merged["strings"][0], b"abcdef")
        self.assertIsInstance(merged["lengths"], numpy.ndarray)
        self.assertEqual(merged["lengths"].shape, (3,))
        self.assertEqual(merged["lengths"][0], 1)
        self.assertEqual(merged["lengths"][1], 2)
        self.assertEqual(merged["lengths"][2], 3)

    def test_split_bytes(self):
        strings = split_strings({
            "strings": numpy.array([b"abcdef"]),
            "lengths": numpy.array([1, 2, 3]),
            "str": False
        })
        self.assertEqual(strings, [b"a", b"bc", b"def"])

    def test_disassemble_sparse_matrix(self):
        arr = numpy.zeros((10, 10), dtype=numpy.float32)
        numpy.random.seed(0)
        arr[numpy.random.randint(0, 10, (50, 2))] = 1
        mat = csr_matrix(arr)
        dis = disassemble_sparse_matrix(mat)
        self.assertIsInstance(dis, dict)
        self.assertIn("shape", dis)
        self.assertIn("format", dis)
        self.assertIn("data", dis)
        self.assertEqual(dis["shape"], arr.shape)
        self.assertEqual(dis["format"], "csr")
        self.assertIsInstance(dis["data"], (tuple, list))
        self.assertEqual(len(dis["data"]), 3)
        self.assertTrue((dis["data"][0] == mat.data).all())
        self.assertTrue((dis["data"][1] == mat.indices).all())
        self.assertTrue((dis["data"][2] == mat.indptr).all())

    def test_assemble_sparse_matrix(self):
        tree = {
            "shape": (3, 10),
            "format": "csr",
            "data": [numpy.arange(1, 8),
                     numpy.array([0, 4, 1, 5, 2, 3, 8]),
                     numpy.array([0, 2, 4, 7])]
        }
        mat = assemble_sparse_matrix(tree)
        self.assertIsInstance(mat, csr_matrix)
        self.assertTrue((mat.data == tree["data"][0]).all())
        self.assertTrue((mat.indices == tree["data"][1]).all())
        self.assertTrue((mat.indptr == tree["data"][2]).all())
        self.assertEqual(mat.shape, (3, 10))
        self.assertEqual(mat.dtype, numpy.int)

    def test_pickle(self):
        docfreq = GenericModel(source=get_path(self.DOCFREQ_PATH))
        res = pickle.dumps(docfreq)
        docfreq_rec = pickle.loads(res)

        for k in docfreq.__dict__:
            self.assertEqual(docfreq.__dict__[k], docfreq_rec.__dict__[k])

    def test_write(self):
        model = Model()
        model._meta = generate_meta("test", (1, 0, 3))
        with tempfile.NamedTemporaryFile() as tmp:
            model._write_tree({"xxx": 100500}, tmp.name)
            with asdf.open(tmp.name) as f:
                self.assertEqual(f.tree["meta"]["model"], "test")
                self.assertEqual(f.tree["xxx"], 100500)
                self.assertEqual(oct(os.stat(tmp.name).st_mode)[-3:], "666")

    def test_write_fileobj(self):
        model = Model()
        model._meta = generate_meta("test", (1, 0, 3))
        buffer = BytesIO()
        model._write_tree({"xxx": 100500}, buffer)
        buffer.seek(0)
        with asdf.open(buffer) as f:
            self.assertEqual(f.tree["meta"]["model"], "test")
            self.assertEqual(f.tree["xxx"], 100500)

    def test_load_fileobj(self):
        path = get_path(self.DOCFREQ_PATH)
        buffer = BytesIO()
        with open(path, "rb") as fin:
            buffer.write(fin.read())
        buffer.seek(0)
        model = Model1().load(source=buffer)
        self.assertEqual(model.created_at, datetime.datetime(2017, 6, 19, 9, 59, 14, 766638))


if __name__ == "__main__":
    unittest.main()
