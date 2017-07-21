from datetime import datetime
import uuid


ARRAY_COMPRESSION = "zlib"


def generate_meta(name: str, version: tuple, *deps) -> dict:
    """
    Creates the metadata tree for the given model name and the list of
    dependencies.

    :param name: The model's name.
    :param version: The caller's version - used to check the format match.
    :param deps: The list of metas this model depends on.
    :return: dict with the metadata.
    """
    return {
        "model": name,
        "uuid": str(uuid.uuid4()),
        "dependencies": [d.meta for d in deps],
        "version": version,
        "created_at": datetime.now()
    }


def _extract_index_meta_dependency(meta):
    return {
        "model": meta["model"],
        "uuid": meta["uuid"],
        "dependencies": [_extract_index_meta_dependency(m)
                         for m in meta["dependencies"]],
        "version": meta["version"],
        "created_at": str(meta["created_at"]),
    }


def extract_index_meta(meta: dict, model_url: str) -> dict:
    """
    Converts the metadata tree into a dict which is suitable for index.json.

    :param meta: tree["meta"] :class:`dict`.
    :param model_url: public URL of the model
    :return: converted dict.
    """
    result = _extract_index_meta_dependency(meta)
    del result["model"]
    del result["uuid"]
    result["url"] = model_url
    return result
