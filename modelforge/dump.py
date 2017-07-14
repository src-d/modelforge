import logging
from pprint import pprint

from modelforge.backends import create_backend_noexc
from modelforge.model import GenericModel


def dump_model(args):
    """
    Prints the information about the model.

    :param args: :class:`argparse.Namespace` with "input", "backend", "args" and \
                 "log_level".
    :return: None
    """
    log = logging.getLogger("dump")
    backend = create_backend_noexc(log, args.backend, args.args)
    if backend is None:
        return 1
    model = GenericModel(args.input, backend=backend,
                         log_level=logging._nameToLevel[args.log_level])
    pprint(model.meta)
