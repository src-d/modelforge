import logging
import unittest

from modelforge import slogging
from modelforge.tests.capture import captured_output


class LogTests(unittest.TestCase):
    def test_setup(self):
        with captured_output() as (out, err, log):
            root = logging.getLogger()
            if len(root.handlers) == 1:
                root.handlers.insert(0, logging.StreamHandler())
            slogging.setup("INFO", False)
            logger = logging.getLogger("test")
            logger.info("success")
        self.assertIn("test", err.getvalue())
        self.assertIn("success", err.getvalue())
        self.assertIn("1;36", err.getvalue())


if __name__ == "__main__":
    unittest.main()
