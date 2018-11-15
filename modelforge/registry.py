import argparse
import json
import logging
import os

from dateutil.parser import parse as parse_datetime

from modelforge.backends import supply_backend
from modelforge.index import GitIndex
from modelforge.meta import extract_model_meta
from modelforge.models import GenericModel
from modelforge.storage_backend import ExistingBackendError, ModelAlreadyExistsError, \
    StorageBackend


@supply_backend(index_exists=True)
def initialize_registry(args: argparse.Namespace, backend: StorageBackend, log: logging.Logger):
    """
    Initialize the registry and the index.

    :param args: :class:`argparse.Namespace` with "backend", "args", "force" and "log_level".
    :param backend: Backend which is responsible for working with model files.
    :param log: Logger supplied by supply_backend
    :return: None
    """
    try:
        backend.reset(args.force)
    except ExistingBackendError:
        return 1

    log.info("Resetting the index ...")
    backend.index.reset()
    try:
        backend.index.upload("reset", {})
    except ValueError:
        return 1
    log.info("Successfully initialized")


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
    try:
        print(GenericModel(args.input, backend=backend))
    except ValueError as e:
        log.critical('"input" must be a path: %s', e)
        return 1
    except Exception as e:
        log.critical("Failed to load the model: %s: %s" % (type(e).__name__, e))
        return 1


@supply_backend
def publish_model(args: argparse.Namespace, backend: StorageBackend, log: logging.Logger):
    """
    Push the model to Google Cloud Storage and updates the index file.

    :param args: :class:`argparse.Namespace` with "model", "backend", "args", "force", "meta" \
                 "update_default", "username", "password", "remote_repo", "template_model", \
                 "template_readme" and "log_level".
    :param backend: Backend which is responsible for working with model files.
    :param log: Logger supplied by supply_backend
    :return: None if successful, 1 otherwise.
    """
    path = os.path.abspath(args.model)
    try:
        model = GenericModel(source=path, dummy=True)
    except ValueError as e:
        log.critical('"model" must be a path: %s', e)
        return 1
    except Exception as e:
        log.critical("Failed to load the model: %s: %s" % (type(e).__name__, e))
        return 1
    base_meta = model.meta
    try:
        model_url = backend.upload_model(path, base_meta, args.force)
    except ModelAlreadyExistsError:
        return 1

    log.info("Uploaded as %s", model_url)
    with open(os.path.join(args.meta), encoding="utf-8") as _in:
        extra_meta = json.load(_in)
    model_type, model_uuid = base_meta["model"], base_meta["uuid"]
    meta = extract_model_meta(base_meta, extra_meta, model_url)
    log.info("Updating the models index...")
    try:
        template_model = backend.index.load_template(args.template_model)
        template_readme = backend.index.load_template(args.template_readme)
    except ValueError:
        return 1
    backend.index.add_model(model_type, model_uuid, meta, template_model, args.update_default)
    backend.index.update_readme(template_readme)
    try:
        backend.index.upload("add", {"model": model_type, "uuid": model_uuid})
    except ValueError:  # TODO: replace with PorcelainError, see related TODO in index.py:181
        return 1
    log.info("Successfully published.")


def list_models(args: argparse.Namespace):
    """
    Output the list of known models in the registry.

    :param args: :class:`argparse.Namespace` with "username", "password", "remote_repo" and \
                        "log_level"
    :return: None
    """
    try:
        git_index = GitIndex(remote=args.index_repo, username=args.username,
                             password=args.password, cache=args.cache, log_level=args.log_level)
    except ValueError:
        return 1
    for model_type, models in git_index.models.items():
        print(model_type)
        default = git_index.meta[model_type]["default"]
        for uuid, model in sorted(models.items(),
                                  key=lambda m: parse_datetime(m[1]["created_at"]),
                                  reverse=True):
            print("  %s %s" % ("*" if default == uuid else " ", uuid),
                  model["created_at"])


@supply_backend
def delete_model(args: argparse.Namespace, backend: StorageBackend, log: logging.Logger):
    """
    Delete a model.

    :param args: :class:`argparse.Namespace` with "input", "backend", "args", "meta", \
                        "update_default", "username", "password", "remote_repo", \
                        "template_model", "template_readme" and "log_level".
    :param backend: Backend which is responsible for working with model files.
    :param log: Logger supplied by supply_backend
    :return: None
    """
    try:
        meta = backend.index.remove_model(args.input)
        template_readme = backend.index.load_template(args.template_readme)
        backend.index.update_readme(template_readme)
    except ValueError:
        return 1
    backend.delete_model(meta)
    log.info("Updating the models index...")
    try:
        backend.index.upload("delete", meta)
    except ValueError:  # TODO: replace with PorcelainError
        return 1
    log.info("Successfully deleted.")
