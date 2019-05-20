import logging
import math
import os
from typing import BinaryIO, Union

import requests

from modelforge.progress_bar import progress_bar


DEFAULT_DOWNLOAD_CHUNK_SIZE = 65536


def download(source: str, file: Union[str, BinaryIO], log: logging.Logger,
             chunk_size: int = -1) -> None:
    """
    Download a file from an HTTP source.

    :param source: URL to fetch.
    :param file: Where to store the downloaded data.
    :param log: Logger.
    :param chunk_size: Size of the download buffer.
    """
    log.info("Fetching %s...", source)
    if chunk_size < 0:
        chunk_size = DEFAULT_DOWNLOAD_CHUNK_SIZE
    r = requests.get(source, stream=True)
    if r.status_code != 200:
        log.error(
            "An error occurred while fetching the model, with code %s" % r.status_code)
        raise ValueError
    if isinstance(file, str):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        f = open(file, "wb")
    else:
        f = file
    try:
        total_length = int(r.headers.get("content-length"))
        num_chunks = math.ceil(total_length / chunk_size)
        if num_chunks == 1:
            f.write(r.content)
        else:
            for chunk in progress_bar(
                    r.iter_content(chunk_size=chunk_size),
                    log,
                    expected_size=num_chunks):
                if chunk:
                    f.write(chunk)
    finally:
        if isinstance(file, str):
            f.close()
