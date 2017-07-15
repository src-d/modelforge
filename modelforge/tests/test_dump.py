import argparse
import os
import unittest

from modelforge.dump import dump_model
import modelforge.gcs_backend as gcs_backend
from modelforge.model import Model
import modelforge.models as models
from modelforge.tests.capture import captured_output
from modelforge.tests.fake_requests import FakeRequests


@models.register_model
class TestModel(Model):
    NAME = "docfreq"

    def load(self, tree):
        self.docs = tree["docs"]

    def dump(self):
        return str(self.docs)


class DumpTests(unittest.TestCase):
    DOCFREQ_DUMP = """{'created_at': datetime.datetime(2017, 6, 19, 9, 59, 14, 766638),
 'dependencies': [],
 'model': 'docfreq',
 'uuid': 'f64bacd4-67fb-4c64-8382-399a8e7db52a',
 'version': [1, 0, 0]}
1000
"""
    DOCFREQ_PATH = "test.asdf"

    def test_docfreq(self):
        with captured_output() as (out, _, _):
            dump_model(self._get_args(input=self._get_path(self.DOCFREQ_PATH)))
        self.assertEqual(out.getvalue(), self.DOCFREQ_DUMP)

    def test_docfreq_id(self):
        def route(url):
            if url.endswith(gcs_backend.GCSBackend.INDEX_FILE):
                return '{"models": {"docfreq": {' \
                       '"f64bacd4-67fb-4c64-8382-399a8e7db52a": ' \
                       '{"url": "https://xxx"}}}}'.encode()
            self.assertEqual("https://xxx", url)
            with open(self._get_path(self.DOCFREQ_PATH), "rb") as fin:
                return fin.read()

        gcs_backend.requests = FakeRequests(route)
        with captured_output() as (out, err, _):
            dump_model(self._get_args(
                input="f64bacd4-67fb-4c64-8382-399a8e7db52a"))
        self.assertEqual(out.getvalue(), self.DOCFREQ_DUMP)
        self.assertFalse(err.getvalue())

    def test_docfreq_url(self):
        def route(url):
            self.assertEqual("https://xxx", url)
            with open(self._get_path(self.DOCFREQ_PATH), "rb") as fin:
                return fin.read()

        gcs_backend.requests = FakeRequests(route)
        with captured_output() as (out, _, _):
            dump_model(self._get_args(input="https://xxx"))
        self.assertEqual(out.getvalue(), self.DOCFREQ_DUMP)

    @staticmethod
    def _get_args(input=None):
        return argparse.Namespace(input=input, backend=None, args=None, log_level="WARNING")

    @staticmethod
    def _get_path(name):
        return os.path.join(os.path.dirname(__file__), name)


if __name__ == "__main__":
    unittest.main()
