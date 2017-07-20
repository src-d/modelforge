import argparse
import sys
import unittest


import modelforge.__main__ as main


class MainTests(unittest.TestCase):
    def test_handlers(self):
        handlers = [False] * 4

        def validate_args(args):
            self.assertTrue(hasattr(args, "backend"))
            self.assertTrue(hasattr(args, "args"))

        def dump_model(args):
            validate_args(args)
            handlers[0] = True

        def publish_model(args):
            validate_args(args)
            handlers[1] = True

        def list_models(args):
            validate_args(args)
            handlers[2] = True

        def initialize_registry(args):
            validate_args(args)
            handlers[3] = True

        main.dump_model = dump_model
        main.publish_model = publish_model
        main.list_models = list_models
        main.initialize_registry = initialize_registry
        args = sys.argv
        error = argparse.ArgumentParser.error
        argparse.ArgumentParser.error = lambda self, message: None

        for action in ("dump", "publish", "list", "init"):
            sys.argv = [main.__file__, action]
            main.main()

        sys.argv = args
        argparse.ArgumentParser.error = error
        self.assertEqual(sum(handlers), 4)

if __name__ == "__main__":
    unittest.main()
