import argparse
import logging

from modelforge.registry import supply_backend
from modelforge.storage_backend import StorageBackend
import modelforge.models as models


@supply_backend("dump")
def dump_model(args: argparse.Namespace, backend: StorageBackend, log: logging.Logger):
    """
    Prints the information about the model.

    :param args: :class:`argparse.Namespace` with "input", "backend", "args" and \
                 "log_level".
    :return: None
    """
    print(models.GenericModel(args.input, backend=backend))
