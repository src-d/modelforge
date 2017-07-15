import argparse
import logging
import sys

from modelforge.logs import setup_logging
from modelforge.registry import publish_model, list_models, initialize_registry
from modelforge.dump import dump_model


def main():
    """
    Creates all the argparse-rs and invokes the function from set_defaults().

    :return: The result of the function from set_defaults().
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", default="INFO",
                        choices=logging._nameToLevel,
                        help="Logging verbosity.")
    subparsers = parser.add_subparsers(help="Commands", dest="command")

    def add_backend_args(p):
        p.add_argument("--backend", default=None, help="Backend to use.")
        p.add_argument("--args", default=None, help="Backend's arguments.")

    dump_parser = subparsers.add_parser(
        "dump", help="Print a brief information about the model to stdout.")
    dump_parser.set_defaults(handler=dump_model)
    dump_parser.add_argument(
        "input", help="Path to the model file, URL or UUID.")
    add_backend_args(dump_parser)

    publish_parser = subparsers.add_parser(
        "publish", help="Upload the model to the cloud and update the "
                        "registry.")
    publish_parser.set_defaults(handler=publish_model)
    publish_parser.add_argument(
        "model", help="The path to the model to publish.")
    add_backend_args(publish_parser)
    publish_parser.add_argument("-d", "--update-default", action="store_true",
                                help="Set this model as the default one.")
    publish_parser.add_argument("--force", action="store_true",
                                help="Overwrite existing models.")

    list_parser = subparsers.add_parser(
        "list", help="Lists all the models in the registry.")
    list_parser.set_defaults(handler=list_models)
    add_backend_args(list_parser)

    init_parser = subparsers.add_parser("init", help="Initialize the registry.")
    init_parser.set_defaults(handler=initialize_registry)
    add_backend_args(init_parser)

    args = parser.parse_args()
    args.log_level = logging._nameToLevel[args.log_level]
    setup_logging(args.log_level)
    try:
        handler = args.handler
    except AttributeError:
        def print_usage(_):
            parser.print_usage()

        handler = print_usage
    return handler(args)

if __name__ == "__main__":
    sys.exit(main())
