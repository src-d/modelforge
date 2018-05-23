import argparse
import logging

from modelforge.backends import supply_backend
from modelforge.storage_backend import StorageBackend
from modelforge.model import Model


@supply_backend
def delete_model(args: argparse.Namespace, backend: StorageBackend, log: logging.Logger):
    """
    Deletes a model.

    :param args: :class:`argparse.Namespace` with "input", "backend", "args" and \
                 "log_level".
    :return: None
    """
    index = backend.fetch_index()
    meta = {"uuid": args.input, "model": None}
    for key, val in index["models"].items():
        if meta["uuid"] in val:
            log.info("Found %s in %s model storage" % (meta["uuid"], key))
            meta["model"] = key
            break
    if meta["model"] is None:
        log.error("Model not found, aborted.")
        return 1
    if "default" in index["models"][meta["model"]] and \
            index["models"][meta["model"]][Model.DEFAULT_NAME] == meta["uuid"]:
        log.info("Model is set as default, removing from index ...")
        index["models"][meta["model"]].pop(Model.DEFAULT_NAME)
    if len(index["models"][meta["model"]]) == 1:
        index["models"].pop(meta["model"])
    else:
        index["models"][meta["model"]].pop(meta["uuid"])
    backend.delete_model(meta)
    log.info("Updating the models index...")
    backend.upload_index(index)
