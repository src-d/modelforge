import logging
import unittest

from modelforge.logs import setup_logging
from modelforge.tests.capture import captured_output


class LogTests(unittest.TestCase):
    def test_setup(self):
        with captured_output() as (out, err, log):
            root = logging.getLogger()
            if len(root.handlers) == 1:
                root.handlers.insert(0, logging.StreamHandler())
            setup_logging("INFO")
            logger = logging.getLogger("test")
            logger.info("success")
        self.assertIn("test", err.getvalue())
        self.assertIn("success", err.getvalue())
        self.assertIn("1;36", err.getvalue())


if __name__ == "__main__":
    unittest.main()
