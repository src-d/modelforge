import logging
from typing import Type
from functools import wraps

import modelforge.configuration as config
from modelforge.gcs_backend import GCSBackend
from modelforge.index import GitIndex
from modelforge.storage_backend import StorageBackend

__registry__ = {b.NAME: b for b in (GCSBackend,)}


def register_backend(cls: Type[StorageBackend]):
    if not issubclass(cls, StorageBackend):
        raise TypeError("cls must be a subclass of StorageBackend")
    __registry__[cls.NAME] = cls
    return cls


def create_backend(name: str=None, git_index: GitIndex=None, args: str=None):
    if name is None:
        name = config.BACKEND
    if not args:
        args = config.BACKEND_ARGS
    if args:
        try:
            kwargs = dict(p.split("=") for p in args.split(","))
        except:  # flake8: noqa
            raise ValueError("Invalid args") from None
    else:
        kwargs = {}
    if git_index is None:
        git_index = GitIndex()
    kwargs["index"] = git_index
    return __registry__[name](**kwargs)


def create_backend_noexc(log: logging.Logger, name: str=None, git_index: GitIndex=None,
                         args: str=None):
    try:
        return create_backend(name, git_index, args)
    except KeyError:
        log.critical("No such backend: %s (looked in %s)",
                     name, list(__registry__.keys()))
        return None
    except ValueError:
        log.critical("Invalid backend arguments: %s", args)
        return None


def supply_backend(optional: bool=False, init: bool=False):
    """
    Used by command line entries.
    """
    real_optional = False if callable(optional) else optional

    def supply_backend_inner(func):
        @wraps(func)
        def wrapped_supply_backend(args):
            log = logging.getLogger(func.__name__)
            if real_optional and not getattr(args, "backend", False):
                backend = None
            else:
                try:
                    git_index = GitIndex(index_repo=args.index_repo, username=args.username,
                                         password=args.password, cache=args.cache, init=init,
                                         signoff=args.signoff, log_level=args.log_level)
                except ValueError:
                    return 1
                backend = create_backend_noexc(log, args.backend, git_index, args.args)
                if backend is None:
                    return 1
            return func(args, backend, log)
        return wrapped_supply_backend
    if callable(optional):
        return supply_backend_inner(optional)
    return supply_backend_inner
