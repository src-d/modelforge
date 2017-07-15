import logging

from modelforge.backends import create_backend_noexc
import modelforge.models as models


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
    print(models.GenericModel(args.input, backend=backend))
