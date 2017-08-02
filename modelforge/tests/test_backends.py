import logging
import unittest

from modelforge import backends


class BackendsTests(unittest.TestCase):
    def test_register_backend(self):
        class Foo:
            pass

        with self.assertRaises(TypeError):
            backends.register_backend(Foo)

        class Bar(backends.StorageBackend):
            NAME = "Bar"

        backends.register_backend(Bar)
        self.assertEqual(Bar, backends.__registry__["Bar"])

    def test_create_backend_invalid_args(self):
        backup = backends.config.BACKEND_ARGS
        backends.config.BACKEND_ARGS = "lalala"

        try:
            with self.assertRaises(ValueError):
                backends.create_backend("Bar")
        finally:
            backends.config.BACKEND_ARGS = backup

        backup = backends.config.BACKEND_ARGS
        backends.config.BACKEND_ARGS = ""

        class Bar(backends.StorageBackend):
            NAME = "Bar"
        backends.register_backend(Bar)

        try:
            self.assertIsInstance(backends.create_backend("Bar"), Bar)
        finally:
            backends.config.BACKEND_ARGS = backup

    def test_create_backend_noexc(self):
        backup = backends.config.BACKEND_ARGS
        backends.config.BACKEND_ARGS = "lalala"
        logger = logging.getLogger()

        try:
            self.assertIsNone(backends.create_backend_noexc(logger, "Bar"))
        finally:
            backends.config.BACKEND_ARGS = backup

        self.assertIsNone(backends.create_backend_noexc(logger, "Bar!!!"))

if __name__ == "__main__":
    unittest.main()
