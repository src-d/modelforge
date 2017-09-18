import logging
from typing import Type

import modelforge.configuration as config
from modelforge.gcs_backend import GCSBackend
from modelforge.storage_backend import StorageBackend

__registry__ = {b.NAME: b for b in (GCSBackend,)}


def register_backend(cls: Type[StorageBackend]):
    if not issubclass(cls, StorageBackend):
        raise TypeError("cls must be a subclass of StorageBackend")
    __registry__[cls.NAME] = cls
    return cls


def create_backend(name: str=None, args: str=None):
    if name is None:
        name = config.BACKEND
    if not args:
        args = config.BACKEND_ARGS
    if args:
        try:
            kwargs = dict(p.split("=") for p in args.split(","))
        except:
            raise ValueError("Invalid args") from None
    else:
        kwargs = {}
    return __registry__[name](**kwargs)


def create_backend_noexc(log: logging.Logger, name: str=None, args: str=None):
    try:
        return create_backend(name, args)
    except KeyError:
        log.critical("No such backend: %s (looked in %s)",
                     name, list(__registry__.keys()))
        return None
    except ValueError:
        log.critical("Invalid backend arguments: %s", args)
        return None
