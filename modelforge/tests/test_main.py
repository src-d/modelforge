import argparse
import sys
import unittest


import modelforge.__main__ as main


class MainTests(unittest.TestCase):
    def test_handlers(self):
        handlers = [False] * 5

        def backend_args(args):
            self.assertTrue(hasattr(args, "backend"))
            self.assertTrue(hasattr(args, "args"))

        def index_args(args):
            self.assertTrue(hasattr(args, "index_repo"))
            self.assertTrue(hasattr(args, "cache"))
            self.assertTrue(hasattr(args, "username"))
            self.assertTrue(hasattr(args, "password"))

        def template_args(args):
            self.assertTrue(hasattr(args, "template_model"))
            self.assertTrue(hasattr(args, "template_readme"))

        def dump_model(args):
            self.assertTrue(hasattr(args, "input"))
            backend_args(args)
            index_args(args)
            handlers[0] = True

        def publish_model(args):
            self.assertTrue(hasattr(args, "model"))
            self.assertTrue(hasattr(args, "meta"))
            self.assertTrue(hasattr(args, "force"))
            self.assertTrue(hasattr(args, "update_default"))
            backend_args(args)
            index_args(args)
            template_args(args)
            handlers[1] = True

        def list_models(args):
            index_args(args)
            handlers[2] = True

        def initialize_registry(args):
            self.assertTrue(hasattr(args, "force"))
            backend_args(args)
            index_args(args)
            handlers[3] = True

        def delete_model(args):
            self.assertTrue(hasattr(args, "input"))
            backend_args(args)
            index_args(args)
            template_args(args)
            handlers[4] = True

        main.dump_model = dump_model
        main.publish_model = publish_model
        main.list_models = list_models
        main.initialize_registry = initialize_registry
        main.delete_model = delete_model
        args = sys.argv
        error = argparse.ArgumentParser.error
        argparse.ArgumentParser.error = lambda self, message: None

        for action in ("dump", "publish", "list", "init", "delete"):
            sys.argv = [main.__file__, action]
            main.main()

        sys.argv = args
        argparse.ArgumentParser.error = error
        self.assertEqual(sum(handlers), 5)


if __name__ == "__main__":
    unittest.main()
