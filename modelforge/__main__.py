import argparse
import logging
import os
import sys

from modelforge import slogging
from modelforge.registry import delete_model, dump_model, initialize_registry, list_models, \
    publish_model


def main():
    """
    Create all the argparse-rs and invokes the function from set_defaults().

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

    def add_index_args(p):
        p.add_argument("--username", default="",
                       help="Username for the Git repository with the index.")
        p.add_argument("--password", default="",
                       help="Password for the Git repository with the index.")
        p.add_argument("--index-repo", default=None,
                       help="Url of the remote Git repository.")
        p.add_argument("--cache", default=None,
                       help="Path to the folder where the Git repository will be cached.")
        p.add_argument("-s", "--signoff", action="store_true",
                       help="Add Signed-off-by line by the committer at the end of the commit log "
                            "message. The meaning of a signoff depends on the project, but it "
                            "typically certifies that committer has the rights to submit this work"
                            " under the same license and agrees to a Developer Certificate of "
                            "Origin (see http://developercertificate.org/ for more information).")

    def add_templates_args(p):
        p.add_argument(
            "--template-model",
            default=os.path.join(os.path.dirname(__file__), "templates/template_model.md.jinja2"),
            help="Path to the jinja2 template used in the index for the model.")
        p.add_argument(
            "--template-readme",
            default=os.path.join(os.path.dirname(__file__), "templates/template_readme.md.jinja2"),
            help="Path to the jinja2 template used in the index for the readme.")

    # ------------------------------------------------------------------------
    init_parser = subparsers.add_parser("init", help="Initialize the registry.")
    init_parser.set_defaults(handler=initialize_registry)
    init_parser.add_argument("-f", "--force", action="store_true",
                             help="Destructively initialize the registry.")
    add_index_args(init_parser)
    add_backend_args(init_parser)
    # ------------------------------------------------------------------------
    dump_parser = subparsers.add_parser(
        "dump", help="Print a brief information about the model to stdout.")
    dump_parser.set_defaults(handler=dump_model)
    dump_parser.add_argument(
        "input", help="Path to the model file, URL or UUID.")
    add_index_args(dump_parser)
    add_backend_args(dump_parser)
    # ------------------------------------------------------------------------
    publish_parser = subparsers.add_parser(
        "publish", help="Upload the model and update the registry.")
    publish_parser.set_defaults(handler=publish_model)
    publish_parser.add_argument(
        "model", help="The path to the model to publish.")
    publish_parser.add_argument(
        "--meta", default=os.path.join(os.path.dirname(__file__), "templates/template_meta.json"),
        help="Path to the JSON file which contains the additional metadata of the model.")
    publish_parser.add_argument("-d", "--update-default", action="store_true",
                                help="Set this model as the default one.")
    publish_parser.add_argument("-f", "--force", action="store_true",
                                help="Overwrite existing models.")
    add_index_args(publish_parser)
    add_backend_args(publish_parser)
    add_templates_args(publish_parser)
    # ------------------------------------------------------------------------
    list_parser = subparsers.add_parser(
        "list", help="Lists all the models in the registry.")
    list_parser.set_defaults(handler=list_models)
    add_index_args(list_parser)
    # ------------------------------------------------------------------------
    delete_parser = subparsers.add_parser("delete", help="Delete a model.")
    delete_parser.set_defaults(handler=delete_model)
    delete_parser.add_argument(
        "input", help="UUID of the model to be deleted.")
    add_index_args(delete_parser)
    add_backend_args(delete_parser)
    add_templates_args(delete_parser)
    # ------------------------------------------------------------------------
    args = parser.parse_args()
    args.log_level = logging._nameToLevel[args.log_level]
    slogging.setup(args.log_level, False)
    try:
        handler = args.handler
    except AttributeError:
        def print_usage(_):
            parser.print_usage()

        handler = print_usage
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
