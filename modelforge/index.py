import os
import json
import shutil
import logging
import requests
import humanize

from jinja2 import Template
from dulwich import porcelain as git
from dulwich.repo import Repo
from dulwich.errors import HangupException, GitProtocolError, NotGitRepository

from modelforge.configuration import DEFAULT_REPO
from modelforge.meta import extract_index_meta
from modelforge.models import Model

INDEX_FILE = "index.json"  #: Models repository index file name.
DEFAULT_PROTOCOL = "https"
DEFAULT_DOMAIN = "github.com"
DEFAULT_CACHE = os.path.expanduser("~/.cache")
REMOTE_URL = "%s://%s%s/%s"  #: Remote repo url
README_KEYS = {"default", "description", "code"}


class GitIndex:

    COMMIT_MESSAGES = {
        "initilialize": "Initialize a new Modelforge index",
        "delete": "Delete {model_type}/{model_uuid}",
        "add": "Add {model_type}/{model_uuid}",
    }

    def __init__(self, protocol: str=DEFAULT_PROTOCOL, domain: str=DEFAULT_DOMAIN,
                 repo: str=DEFAULT_REPO, username: str="", password: str="",
                 cache: str=DEFAULT_CACHE, log_level: int=logging.INFO):
        """
        Initializes a new instance of :class:`GitIndex`.

        :param protocol: Protocol to use, either http(s), tcp or ssh
        :param domain: Domain name, defaults to github.com
        :param repo: Remote repo to use for index, defaults to the one set by configuration.py file
        :param username: Username for credentials if protocol is not ssh
        :param password: Password for credentials if protocol is not ssh
        :param log_level: The logging level of this instance.
        :raise ValueError: If missing credential, incorrect domain or incorrect credentials
        """
        self._log = logging.getLogger("GitIndex")
        self._log.setLevel(log_level)
        self.repo = repo
        self.cached_repo = os.path.join(cache, repo)
        auth = ""
        if protocol in ("ssh", "git+ssh"):
            auth += "git@"
        elif username and password:
            auth += username + ":" + password + "@"
        elif username or password:
            raise ValueError("Both username and password must be supplied to access git with "
                             "credentials.")
        self.remote_url = REMOTE_URL % (protocol, auth, domain, repo)
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

    def fetch_index(self):
        os.makedirs(os.path.dirname(self.cached_repo), exist_ok=True)
        if not os.path.exists(self.cached_repo):
            self._log.warning("Index not found, caching %s in %s", (self.repo, self.cached_repo))
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
        node = self.models[model_type]
        if Model.DEFAULT_NAME in node and model_uuid == node[Model.DEFAULT_NAME]:
            self._log.info("Model is set as default, removing from index ...")
            node.pop(Model.DEFAULT_NAME)
        model_directory = os.path.join(self.cached_repo, model_type)

        if len(node) == 3:
            self.models.pop(model_type)
            shutil.rmtree(model_directory)
        else:
            node.pop(model_uuid)
            os.remove(os.path.join(model_directory, model_uuid + ".md"))
        return {"model_type": model_type, "model_uuid": model_uuid}

    def add_model(self, model_type: str, model_uuid: str, base_meta: dict, extra_meta: dict,
                  model_url: str, template_model: Template, update_default: bool=False):
        self.models.setdefault(model_type, {})[model_uuid] = \
            extract_index_meta(base_meta, model_url)
        node = self.models[model_type]
        if update_default or len(node) == 1:
            node[Model.DEFAULT_NAME] = model_uuid
        if update_default or len(node) == 2:
            for name in ("code", "description"):
                node[name] = extra_meta[name]
        for key, val in extra_meta["model"].items():
            node[model_uuid].setdefault(key, val)
        model_directory = os.path.join(self.cached_repo, model_type)
        os.makedirs(model_directory, exist_ok=True)
        model = os.path.join(model_directory, model_uuid + ".md")
        if os.path.exists(model):
            os.remove(model)
        response = requests.get(model_url, stream=True)
        size = humanize.naturalsize(int(response.headers["content-length"]))
        links = {}
        for name, items in self.models.items():
            for uuid in items:
                if uuid in extra_meta["model"]["dependencies"]:
                    links[uuid] = os.path.join("/", name, "%s.md" % uuid)
        with open(model, "w") as fout:
            fout.write(template_model.render(base=base_meta, details=extra_meta, links=links,
                       size=size))
        self._log.info("Added %s", model)

    def update_readme(self, template_readme: Template):
        readme = os.path.join(self.cached_repo, "README.md")
        if os.path.exists(readme):
            os.remove(readme)
        links = {}
        for name, items in self.models.items():
            for key in items:
                if key in README_KEYS:
                    continue
                links[key] = os.path.join("/", name, "%s.md" % key)

        with open(readme, "w") as fout:
            fout.write(
                template_readme.render(models=self.models, links=links, metakeys=README_KEYS))
        self._log.info("Updated %s", readme)

    def initialize_index(self):
        for filename in os.listdir(self.cached_repo):
            if ".git" in filename:
                continue
            path = os.path.join(self.cached_repo, filename)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        self.index = {"models": {}}

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
        local_head = Repo(self.cached_repo).head()
        remote_head = git.ls_remote(self.remote_url)[b"HEAD"]
        return local_head != remote_head
