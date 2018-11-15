import os
import sys
import traceback


VENDOR = os.getenv("MODELFORGE_VENDOR", None)
BACKEND = os.getenv("MODELFORGE_BACKEND", None)
BACKEND_ARGS = os.getenv("MODELFORGE_BACKEND_ARGS", "")
INDEX_REPO = os.getenv("MODELFORGE_INDEX_REPO", "")
CACHE_DIR = os.getenv("MODELFORGE_CACHE_DIR",
                      os.path.join(os.path.expanduser("~"), ".cache", "modelforge"))
ALWAYS_SIGNOFF = os.getenv("MODELFORGE_ALWAYS_SIGNOFF", False)

OVERRIDE_FILE = "modelforgecfg.py"


def refresh():
    """Scan over all the involved directories and load configs from them."""
    override_files = []
    for stack in traceback.extract_stack():
        f = os.path.join(os.path.dirname(stack[0]), OVERRIDE_FILE)
        if f not in override_files:
            override_files.insert(0, f)
    if OVERRIDE_FILE in override_files:
        del override_files[override_files.index(OVERRIDE_FILE)]
    override_files.append(OVERRIDE_FILE)

    def import_path(path):
        if sys.version_info < (3, 5, 0):
            from importlib.machinery import SourceFileLoader
            return SourceFileLoader(__name__, path).load_module()
        import importlib.util
        spec = importlib.util.spec_from_file_location(__name__, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    for override_file in override_files:
        if not os.path.isfile(override_file):
            continue
        mod = import_path(override_file)
        globals().update({n: getattr(mod, n) for n in dir(mod) if not n.startswith("__")})


refresh()
