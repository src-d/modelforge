import logging

import modelforge.configuration as config
from modelforge.gcs_backend import GCSBackend


registry = {b.NAME: b for b in (GCSBackend,)}


def create_backend(name: str=None, args: str=None):
    if name is None:
        name = config.BACKEND
    if not args:
        args = config.BACKEND_ARGS
    try:
        kwargs = dict(p.split("=") for p in args.split(","))
    except:
        raise ValueError("Invalid args") from None
    return registry[name](**kwargs)


def create_backend_noexc(log: logging.Logger, name: str=None, args: str=None):
    try:
        return create_backend(name, args)
    except KeyError:
        log.critical("No such backend: %s (looked in %s)",
                     name, list(registry.keys()))
        return None
    except ValueError:
        log.critical("Invalid backend arguments: %s", args)
        return None
