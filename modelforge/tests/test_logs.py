import argparse
from distutils.util import strtobool
import logging
import os
import subprocess
import sys
from typing import Tuple, Union
import unittest

from modelforge import slogging
from modelforge.tests.capture import captured_output


ARGPARSE_TEST = "MODELFORGE_SLOGGING_TEST"


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

    def test_argparse(self):
        level, structured, config_path = self.launch_test_slogging_main("", False, "")
        self.assertEqual(level, "INFO")
        self.assertFalse(structured)
        self.assertEqual(config_path, "None")
        level, structured, config_path = self.launch_test_slogging_main("DEBUG", True, "/path")
        self.assertEqual(level, "DEBUG")
        self.assertTrue(structured)
        self.assertEqual(config_path, "/path")

    def test_argparse_no_patch(self):
        parser = argparse.ArgumentParser()
        method = parser.parse_args
        slogging.add_logging_args(parser, False)
        self.assertEqual(method, parser.parse_args)

        parser = argparse.ArgumentParser()
        method = parser.parse_args
        slogging.add_logging_args(parser)
        self.assertNotEqual(method, parser.parse_args)

    def launch_test_slogging_main(self, level: str, structured: bool, config_path: str
                                  ) -> Tuple[str, bool, str]:
        args = [sys.executable, __file__]
        if config_path:
            args.extend(["--log-config", config_path])
        if structured:
            args.append("--log-structured")
        if level:
            args.extend(["--log-level", level])
        patched_env = os.environ.copy()
        patched_env[ARGPARSE_TEST] = "1"
        result = subprocess.check_output(args, env=patched_env).decode().splitlines()
        result[1] = strtobool(result[1])
        return tuple(result)


def run_slogging_main():
    parser = argparse.ArgumentParser()
    slogging.add_logging_args(parser)

    def my_setup(level: Union[str, int], structured: bool, config_path: str):
        print(level)
        print(structured)
        print(config_path)

    slogging.setup = my_setup
    parser.parse_args()


if __name__ == "__main__":
    if os.getenv(ARGPARSE_TEST, False):
        run_slogging_main()
    else:
        unittest.main()
