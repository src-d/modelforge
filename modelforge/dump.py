import logging
from pprint import pprint

from modelforge.model import Model


class GenericModel(Model):
    """
    Compatible with any model.
    """

    def _load(self, tree):
        self.tree = tree


def dump_model(args):
    """
    Prints the information about the model.

    :param args: :class:`argparse.Namespace` with "input", "gcs" and \
                 "log_level".
    :return: None
    """
    model = GenericModel(args.input, gcs_bucket=args.gcs,
                         log_level=logging._nameToLevel[args.log_level])
    pprint(model.meta)
