import argparse
import os
import sys
import unittest
from unittest.mock import patch

from modelforge.environment import collect_env_info
from modelforge.tools import install_environment


class EnvironmentTests(unittest.TestCase):
    def test_collect_env_info(self):
        info = collect_env_info()
        self.assertTrue(info["python"])
        self.assertTrue(info["platform"])
        self.assertGreater(len(info["packages"]), 0)
        pkgs = set(p[0] for p in info["packages"])
        self.assertIn("modelforge", pkgs)
        self.assertIn("asdf", pkgs)
        self.assertIn("numpy", pkgs)

    def test_install_environment(self):
        args = argparse.Namespace()
        args.input = os.path.join(os.path.dirname(__file__), "test.asdf")
        args.reproduce = False
        args.pip = ["-x"]
        mycmdline = []

        def fake_call(cmdline):
            mycmdline.extend(cmdline)

        with patch("subprocess.check_call", fake_call):
            install_environment(args)
        self.assertEqual(mycmdline[0], sys.executable)
        self.assertEqual(mycmdline[1], "-m")
        self.assertEqual(mycmdline[2], "pip")
        self.assertEqual(mycmdline[3], "install")
        self.assertEqual(mycmdline[4], "-x")
        self.assertTrue(mycmdline[5].startswith("Jinja2==2.10"))


if __name__ == "__main__":
    unittest.main()
