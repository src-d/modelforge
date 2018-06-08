import os
import json
from copy import deepcopy
from dulwich.errors import HangupException, GitProtocolError, NotGitRepository
import modelforge.index as ind


def clone(remote_url, cached_repo, checkout=True):
    if "bad-url-1" in remote_url:
        raise HangupException
    if "bad-url-2" in remote_url:
        raise GitProtocolError
    if "bad-url-3" in remote_url:
        raise NotGitRepository
    os.makedirs(cached_repo, exist_ok=True)
    with open(os.path.join(cached_repo, ind.INDEX_FILE), "w") as _out:
        json.dump(FakeRepo.index, _out)
    df_dir = os.path.join(cached_repo, "docfreq")
    os.mkdir(df_dir)
    with open(os.path.join(df_dir, "12345678-9abc-def0-1234-56789abcdef0.md"), "w") as _out:
        _out.write("test")
    with open(os.path.join(df_dir, "1e3da42a-28b6-4b33-94a2-a5671f4102f4.md"), "w") as _out:
        _out.write("test")
    FakeRepo.remote_url = remote_url
    FakeRepo.checkout = checkout


def pull(remote_url, cached_repo):
    FakeRepo.remote_head = "0"
    FakeRepo.pulled = True


def add():
    FakeRepo.added = True


def ls_remote(remote_url):
    return {b"HEAD": "0"}


def commit(message):
    FakeRepo.message = message


def push(cached_repo, remote_url, branch):
    FakeRepo.pushed = True


class FakeRepo:
    remote_head = "0"
    uploaded_index = None
    checkout = False
    pulled = False
    added = False
    message = None
    pushed = False
    remote_url = None
    default_index = {
        "models": {
            "docfreq": {
                "code": "%s",
                "description": "",
                "default": "12345678-9abc-def0-1234-56789abcdef0",
                "12345678-9abc-def0-1234-56789abcdef0": {
                    "url": "https://xxx",
                    "created_at": "13:00"},
                "1e3da42a-28b6-4b33-94a2-a5671f4102f4": {
                    "url": "https://xxx",
                    "created_at": "13:00"}}}}
    index = deepcopy(default_index)

    def __init__(self, cached_repo):
        pass

    def head(self):
        return FakeRepo.remote_head

    @classmethod
    def reset(cls):
        cls.uploaded_index = None
        cls.remote_head = "0"
        cls.checkout = False
        cls.pulled = False
        cls.added = False
        cls.message = None
        cls.pushed = False
        cls.remote_url = None
        cls.index = deepcopy(cls.default_index)
