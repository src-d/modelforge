import argparse
import logging
import subprocess
import sys
from typing import Optional

from modelforge.backends import supply_backend
from modelforge.models import GenericModel
from modelforge.storage_backend import download_http, StorageBackend


@supply_backend(optional=True)
def install_environment(args: argparse.Namespace, backend: StorageBackend, log: logging.Logger):
    """
    Install the packages mentioned in the model's metadata.

    :param args: :param args: :class:`argparse.Namespace` with "input", "reproduce", "backend", \
                 "args", "username", "password", "remote_repo" and "log_level".
    :param backend: Backend which is responsible for working with model files.
    :param log: Logger supplied by supply_backend
    :return: None
    """
    model = _load_generic_model(args.input, backend, log)
    if model is None:
        return 1
    packages = ["%s==%s" % (pkg, ver) for pkg, ver in model.environment["packages"]]
    cmdline = [sys.executable, "-m", "pip", "install"] + args.pip + packages
    log.info(" ".join(cmdline))
    subprocess.check_call(cmdline)
    if args.reproduce:
        for dataset in model.datasets:
            download_http(dataset[0], dataset[1], log)


def _load_generic_model(source: str, backend: StorageBackend, log: logging.Logger
                        ) -> Optional[GenericModel]:
    try:
        return GenericModel(source, backend=backend)
    except ValueError as e:
        log.critical('"input" must be a path: %s', e)
        return None
    except Exception as e:
        log.critical("Failed to load the model: %s: %s" % (type(e).__name__, e))
        return None


@supply_backend(optional=True)
def dump_model(args: argparse.Namespace, backend: StorageBackend, log: logging.Logger):
    """
    Print the information about the model.

    :param args: :class:`argparse.Namespace` with "input", "backend", "args", "username", \
                 "password", "remote_repo" and "log_level".
    :param backend: Backend which is responsible for working with model files.
    :param log: Logger supplied by supply_backend
    :return: None
    """
    model = _load_generic_model(args.input, backend, log)
    if model is None:
        return 1
    print(model)
