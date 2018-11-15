from datetime import datetime
from typing import Sequence
import uuid

import humanize
import requests

ARRAY_COMPRESSION = "zlib"


def generate_meta(name: str, version: Sequence, *deps) -> dict:
    """
    Create the metadata tree for the given model name and the list of dependencies.

    :param name: The model's name.
    :param version: The caller's version - used to check the format match.
    :param deps: The list of metas this model depends on. Can be either models or dicts.
    :return: dict with the metadata.
    """
    return {
        "model": name,
        "uuid": str(uuid.uuid4()),
        "dependencies": [(d.meta if not isinstance(d, dict) else d)
                         for d in deps],
        "version": list(version),
        "created_at": datetime.now()
    }


def extract_model_meta(base_meta: dict, extra_meta: dict, model_url: str) -> dict:
    """
    Merge the metadata from the backend and the extra metadata into a dict which is suitable for \
    index.json.

    :param base_meta: tree["meta"] :class:`dict` containing data from the backend
    :param extra_meta: dict containing data from the user, similar to `template_meta.json`
    :param model_url: public URL of the model
    :return: converted dict.
    """
    meta = {"default": {"default": base_meta["uuid"], "code": extra_meta["code"],
                        "description": extra_meta["description"]}}
    del base_meta["model"]
    del base_meta["uuid"]
    meta["model"] = base_meta
    meta["model"].update(extra_meta["model"])
    response = requests.get(model_url, stream=True)
    meta["model"]["size"] = humanize.naturalsize(int(response.headers["content-length"]))
    meta["model"]["url"] = model_url
    meta["model"]["created_at"] = str(meta["model"]["created_at"])
    return meta
