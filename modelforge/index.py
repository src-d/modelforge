import os
import json
import shutil
import logging

from jinja2 import Template
from dulwich import porcelain as git
from dulwich.repo import Repo
from dulwich.errors import HangupException, GitProtocolError, NotGitRepository
from urllib.parse import urlparse


INDEX_FILE = "index.json"  #: Models repository index file name.
DEFAULT_CACHE = os.path.expanduser("~/.cache")
REMOTE_URL = "%s://%s%s/%s"  #: Remote repo url


class GitIndex:

    COMMIT_MESSAGES = {
        "initilialize": "Initialize a new Modelforge index",
        "delete": "Delete {model}/{uuid}",
        "add": "Add {model}/{uuid}",
    }

    def __init__(self, index_repo: str= "", username: str= "", password: str= "",
                 cache: str=DEFAULT_CACHE, log_level: int=logging.INFO):
        """
        Initializes a new instance of :class:`GitIndex`.

        :param index_repo: Remote repository's address where the index is maintained
        :param username: Username for credentials if protocol is not ssh
        :param password: Password for credentials if protocol is not ssh
        :param cache: Path to the folder where the repo will be cached, defaults to ~/.cache
        :param log_level: The logging level of this instance.
        :raise ValueError: If missing credential, incorrect url or incorrect credentials
        """
        self._log = logging.getLogger(type(self).__name__)
        self._log.setLevel(log_level)
        parsed_url = urlparse(index_repo)
        if not parsed_url.scheme or \
                parsed_url.scheme not in ("git", "git+ssh", "ssh", "http", "https"):
            raise ValueError("Parsed url does not contain a valid protocol.")
        if not parsed_url.netloc:
            raise ValueError("Parsed url does not contain a valid domain.")
        if not parsed_url.path:
            raise ValueError("Parsed url does not contain a valid repository path.")
        self.repo = parsed_url.path
        if self.repo.startswith("/"):
            self.repo = self.repo[1:]
        if self.repo.endswith(".git"):
            self.repo = self.repo[:-4]
        self.cached_repo = os.path.join(cache, self.repo)
        if username and password:
            auth = username + ":" + password + "@"
            self.remote_url = REMOTE_URL % (parsed_url.scheme, auth, parsed_url.netloc, self.repo)
        elif username or password:
            raise ValueError("Both username and password must be supplied to access git with "
                             "credentials.")
        else:
            self.remote_url = index_repo
        self.index = None
        try:
            self.fetch_index()
        except NotGitRepository as e:
            raise ValueError("Repository does not exist: %s" % e) from e
        except HangupException as e:
            raise ValueError("Check SSH is configured, or connection is stable: %s" % e) from e
        except GitProtocolError as e:
            raise ValueError("%s: %s\nCheck your Git credentials." % (type(e), e))
        self.models = self.index["models"]
        self.meta = self.index["meta"]

    def fetch_index(self):
        os.makedirs(os.path.dirname(self.cached_repo), exist_ok=True)
        if not os.path.exists(self.cached_repo):
            self._log.warning("Index not found, caching %s in %s", self.repo, self.cached_repo)
            git.clone(self.remote_url, self.cached_repo, checkout=True)
        else:
            self._log.info("Index is cached")
            if self._are_local_and_remote_heads_different():
                self._log.info("Cached index is not up to date, pulling %s", self. repo)
                git.pull(self.cached_repo, self.remote_url)
        with open(os.path.join(self.cached_repo, INDEX_FILE), encoding="utf-8") as _in:
            self.index = json.load(_in)

    def remove_model(self, model_uuid: str) -> dict:
        model_type = None
        for key, val in self.models.items():
            if model_uuid in val:
                self._log.info("Found %s among %s models.", (model_uuid, key))
                model_type = key
                break
        if model_type is None:
            raise ValueError("Model not found, aborted.")
        model_directory = os.path.join(self.cached_repo, model_type)
        model_node = self.models[model_type]
        meta_node = self.meta[model_type]
        if len(model_node) == 1:
            self.models.pop(model_type)
            self.meta.pop(model_type)
            shutil.rmtree(model_directory)
        else:
            if meta_node["default"] == model_uuid:
                self._log.info("Model is set as default, removing from index ...")
                meta_node["default"] = ""
            model_node.pop(model_uuid)
            os.remove(os.path.join(model_directory, model_uuid + ".md"))
        return {"model": model_type, "uuid": model_uuid}

    def add_model(self, model_type: str, model_uuid: str, meta: dict,
                  template_model: Template, update_default: bool=False):
        if update_default or model_type not in self.meta:
            self.meta[model_type] = meta["default"]
        model_meta = meta["model"]
        self.models.setdefault(model_type, {})[model_uuid] = model_meta
        model_directory = os.path.join(self.cached_repo, model_type)
        os.makedirs(model_directory, exist_ok=True)
        model = os.path.join(model_directory, model_uuid + ".md")
        if os.path.exists(model):
            os.remove(model)
        links = {model_type: {} for model_type in self.models.keys()}
        for model_type, items in self.models.items():
            for uuid in items:
                if uuid in model_meta["dependencies"]:
                    links[model_type][uuid] = os.path.join("/", model_type, "%s.md" % uuid)
        with open(model, "w") as fout:
            fout.write(template_model.render(model_type=model_type, model_uuid=model_uuid,
                                             meta=model_meta, links=links))
        self._log.info("Added %s", model)

    def update_readme(self, template_readme: Template):
        readme = os.path.join(self.cached_repo, "README.md")
        if os.path.exists(readme):
            os.remove(readme)
        links = {model_type: {} for model_type in self.models.keys()}
        for model_type, model_uuids in self.models.items():
            for model_uuid in model_uuids:
                links[model_type][model_uuid] = os.path.join("/", model_type, "%s.md" % model_uuid)
        with open(readme, "w") as fout:
            self._log.info(self.meta)
            self._log.info(self.models)
            fout.write(template_readme.render(models=self.models, meta=self.meta, links=links))
        self._log.info("Updated %s", readme)

    def initialize_index(self):
        for filename in os.listdir(self.cached_repo):
            if filename.startswith(".git"):
                continue
            path = os.path.join(self.cached_repo, filename)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        self.index = {"models": {}, "meta": {}}

    def upload_index(self, cmd: str, meta: dict):
        index = os.path.join(self.cached_repo, INDEX_FILE)
        if os.path.exists(index):
            os.remove(index)
        self._log.info("Writing the new index.json ...")
        with open(index, "w") as _out:
            json.dump(self.index, _out)
        # implementation of git add --all is pretty bad, changing directory is the easiest way
        os.chdir(self.cached_repo)
        git.add()
        git.commit(message=self.COMMIT_MESSAGES[cmd].format(**meta))
        self._log.info("Pushing the updated index ...")
        # TODO: change when https://github.com/dulwich/dulwich/issues/631 gets addressed
        git.push(self.cached_repo, self.remote_url, b"master")
        if self._are_local_and_remote_heads_different():
            raise ValueError("Push has failed")

    def load_template(self, template: str) -> Template:
        env = dict(trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=False)
        jinja2_ext = ".jinja2"
        if not template.endswith(jinja2_ext):
            raise ValueError("Template file name must end with %s" % jinja2_ext)
        if not template[:-len(jinja2_ext)].endswith(".md"):
            raise ValueError("Template file should be a Markdown file.")
        with open(template, encoding="utf-8") as fin:
            template_obj = Template(fin.read(), **env)
        template_obj.filename = template
        self._log.info("Loaded %s", template)
        return template_obj

    def _are_local_and_remote_heads_different(self):
        local_head = Repo(self.cached_repo).head
        remote_head = git.ls_remote(self.remote_url)[b"HEAD"]
        return local_head != remote_head
