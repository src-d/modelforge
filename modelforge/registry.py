import logging
import os

from dateutil.parser import parse as parse_datetime

from modelforge.meta import extract_index_meta
from modelforge.model import Model
from modelforge.models import GenericModel
from modelforge.backends import create_backend_noexc


def supply_backend(name):
    def supply_backend_inner(func):
        def wrapped_supply_backend(args):
            log = logging.getLogger(name)
            backend = create_backend_noexc(log, args.backend, args.args)
            if backend is None:
                return 1
            return func(args, backend, log)
        return wrapped_supply_backend
    return supply_backend_inner


@supply_backend("publish")
def publish_model(args, backend, log):
    """
    Pushes the model to Google Cloud Storage and updates the index file.

    :param args: :class:`argparse.Namespace` with "model", "backend", "args", "force" and \
                 "update_default".
    :return: None if successful, 1 otherwise.
    """
    path = os.path.abspath(args.model)
    try:
        model = GenericModel(source=path, dummy=True)
    except ValueError:
        log.critical('"model" must be a path')
        return 1
    except Exception as e:
        log.critical("Failed to load the model: %s: %s" % (type(e).__name__, e))
        return 1
    meta = model.meta
    model_url = backend.upload_model(path, meta, args.force)
    with backend.transaction():
        log.info("Uploaded as %s", model_url)
        log.info("Updating the models index...")
        index = backend.fetch_index()
        index["models"].setdefault(meta["model"], {})[meta["uuid"]] = \
            extract_index_meta(meta, model_url)
        if args.update_default:
            index["models"][meta["model"]][Model.DEFAULT_NAME] = meta["uuid"]
        backend.upload_index(index)


@supply_backend("list")
def list_models(args, backend, log):
    """
    Outputs the list of known models in the registry.

    :param args: :class:`argparse.Namespace` with "backend" and "args".
    :return: None
    """
    index = backend.fetch_index()
    for key, val in index["models"].items():
        print(key)
        default = None
        for mid, meta in val.items():
            if mid == "default":
                default = meta
                break
        for mid, meta in sorted(
                [m for m in val.items() if m[1] != default],
                key=lambda m: parse_datetime(m[1]["created_at"]),
                reverse=True):
            print("  %s %s" % ("*" if default == mid else " ", mid),
                  meta["created_at"])
