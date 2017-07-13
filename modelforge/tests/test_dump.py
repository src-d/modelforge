import argparse
from contextlib import contextmanager
from io import StringIO
import logging
import os
import sys
import unittest

import modelforge.model as model
from modelforge.dump import dump_model
from modelforge.tests.fake_requests import FakeRequests


@contextmanager
def captured_output():
    log = StringIO()
    log_handler = logging.StreamHandler(log)
    logging.getLogger().addHandler(log_handler)
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr, log
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        logging.getLogger().removeHandler(log_handler)


class DumpTests(unittest.TestCase):
    DOCFREQ_DUMP = """{'created_at': datetime.datetime(2017, 6, 19, 9, 59, 14, 766638),
 'dependencies': [],
 'model': 'docfreq',
 'uuid': 'f64bacd4-67fb-4c64-8382-399a8e7db52a',
 'version': [1, 0, 0]}
"""
    DOCFREQ_PATH = "test.asdf"

    def test_docfreq(self):
        with captured_output() as (out, _, _):
            dump_model(self._get_args(input=self._get_path(self.DOCFREQ_PATH)))
        self.assertEqual(out.getvalue(), self.DOCFREQ_DUMP)

    def test_docfreq_id(self):
        def route(url):
            if url.endswith(model.Model.INDEX_FILE):
                return '{"models": {"docfreq": {' \
                       '"f64bacd4-67fb-4c64-8382-399a8e7db52a": ' \
                       '{"url": "https://xxx"}}}}'.encode()
            self.assertEqual("https://xxx", url)
            with open(self._get_path(self.DOCFREQ_PATH), "rb") as fin:
                return fin.read()

        model.requests = FakeRequests(route)
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

        model.requests = FakeRequests(route)
        with captured_output() as (out, _, _):
            dump_model(self._get_args(input="https://xxx"))
        self.assertEqual(out.getvalue(), self.DOCFREQ_DUMP)

    @staticmethod
    def _get_args(input=None, gcs=None):
        return argparse.Namespace(input=input, gcs=gcs, log_level="WARNING")

    @staticmethod
    def _get_path(name):
        return os.path.join(os.path.dirname(__file__), name)


if __name__ == "__main__":
    unittest.main()
