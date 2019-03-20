from datetime import datetime, timezone
import uuid

import humanize
import requests
import spdx

from modelforge.environment import collect_environment_without_packages

LICENSES = {l["id"] for l in spdx.licenses()}.union({"Proprietary"})


def check_license(license: str):
    """
    Ensure that the license identifier is SPDX-compliant (or is "Proprietary").

    :param license: License identifier.
    :return: None
    """
    if license not in LICENSES:
        raise ValueError("license must be an SPDX-compliant identifier or \"Proprietary\"")


def generate_new_meta(name: str, description: str, vendor: str, license: str) -> dict:
    """
    Create the metadata tree for the given model name and the list of dependencies.

    :param name: Name of the model.
    :param description: Description of the model.
    :param vendor: Name of the party which is responsible for support of the model.
    :param license: License identifier.
    :return: dict with the metadata.
    """
    check_license(license)
    return {
        "code": None,
        "created_at": get_datetime_now(),
        "datasets": [],
        "dependencies": [],
        "description": description,
        "vendor": vendor,
        "environment": collect_environment_without_packages(),
        "extra": None,
        "license": license,
        "metrics": {},
        "model": name,
        "parent": None,
        "references": [],
        "series": None,
        "tags": [],
        "uuid": str(uuid.uuid4()),
        "version": [1, 0, 0],
    }


def get_datetime_now() -> datetime:
    """
    Return the current UTC date and time.
    """
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime) -> str:
    """
    Format a datetime object as string.

    :param dt: Date and time to format.
    :return: String representation.
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S%z")


def extract_model_meta(base_meta: dict, extra_meta: dict, model_url: str) -> dict:
    """
    Merge the metadata from the backend and the extra metadata into a dict which is suitable for \
    `index.json`.

    :param base_meta: tree["meta"] :class:`dict` containing data from the backend.
    :param extra_meta: dict containing data from the user, similar to `template_meta.json`.
    :param model_url: public URL of the model.
    :return: converted dict.
    """
    meta = {"default": {"default": base_meta["uuid"],
                        "description": base_meta["description"],
                        "code": extra_meta["code"]}}
    del base_meta["model"]
    del base_meta["uuid"]
    meta["model"] = base_meta
    meta["model"].update({k: extra_meta[k] for k in ("code", "datasets", "references", "tags",
                                                     "extra")})
    response = requests.get(model_url, stream=True)
    meta["model"]["size"] = humanize.naturalsize(int(response.headers["content-length"]))
    meta["model"]["url"] = model_url
    meta["model"]["created_at"] = format_datetime(meta["model"]["created_at"])
    return meta
