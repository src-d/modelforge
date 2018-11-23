import unittest

from modelforge.environment import collect_env_info


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


if __name__ == "__main__":
    unittest.main()
