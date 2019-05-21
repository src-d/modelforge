from functools import wraps
import logging
from typing import BinaryIO, Optional, Type, Union

import modelforge.configuration as config
from modelforge.http_ import download as download_http
from modelforge.index import GitIndex
from modelforge.storage_backend import StorageBackend


__registry__ = {}
__downloaders__ = {"http": download_http, "https": download_http}


def register_backend(cls: Type[StorageBackend]):
    """Decorator to register another StorageBackend using it's `NAME`."""
    if not issubclass(cls, StorageBackend):
        raise TypeError("cls must be a subclass of StorageBackend")
    __registry__[cls.NAME] = cls
    # DOWNLOADERS is expected to be a tuple of tuples, not a dict
    # that's because we want it to be immutable
    # we want immutability because extending class-levels dicts in inheritors is messy
    for key, downloader in getattr(cls, "DOWNLOADERS", tuple()):
        if key in __downloaders__:
            raise TypeError("%s.DOWNLOADERS contain %s which is already set to %s" % (
                cls.__name__, key, __downloaders__[key]))
        __downloaders__[key] = downloader
    return cls


def create_backend(name: str=None, git_index: GitIndex=None, args: str=None) -> StorageBackend:
    """Initialize a new StorageBackend by it's name and the specified model registry."""
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
                         args: str=None) -> Optional[StorageBackend]:
    """Initialize a new Backend, return None if there was a known problem."""
    try:
        return create_backend(name, git_index, args)
    except KeyError:
        log.critical("No such backend: %s (looked in %s)",
                     name, list(__registry__.keys()))
        return None
    except ValueError:
        log.critical("Invalid backend arguments: %s", args)
        return None


def supply_backend(optional: Union[callable, bool]=False, index_exists: bool=True):
    """
    Decorator to pass the initialized backend to the decorated callable. \
    Used by command line entries. If the backend cannot be created, return 1.

    :param optional: Either a decorated function or a value which indicates whether we should \
                     construct the backend object if it does not exist in the wrapped function's \
                     `args`: `True` means we shouldn't.
    :param index_exists: Whether the Git model index exists on the remote side or not.
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
                    git_index = GitIndex(remote=args.index_repo, username=args.username,
                                         password=args.password, cache=args.cache,
                                         exists=index_exists, signoff=args.signoff,
                                         log_level=args.log_level)
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


def download_file(source: str, output: Union[str, BinaryIO], log: logging.Logger,
                  chunk_size: int = -1) -> None:
    """
    Download a file by its URL.

    :param source: URL to fetch.
    :param output: Written file name or file object.
    :param log: Logger to use.
    :param chunk_size: Buffer size, if the underlying downloader supports setting it.
    :return: None
    """
    __downloaders__[source[:source.find("://")]](source, output, log, chunk_size)
