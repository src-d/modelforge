from distutils.sysconfig import get_python_lib
import os
import platform
import site
import sys
from typing import Iterable, List, Tuple, Union

try:
    from pip._internal.utils.misc import get_installed_distributions
except ImportError:
    from pip import get_installed_distributions


_env = None


def collect_environment_without_packages() -> dict:
    """
    Return the version of the Python executable and the running platform.
    """
    return {
        "python": sys.version.replace("\n", ""),
        "packages": [],
        "platform": platform.platform(),
    }


def collect_environment(no_cache: bool = False) -> dict:
    """
    Return the version of the Python executable, the versions of the currently loaded packages \
    and the running platform.

    The result is cached unless `no_cache` is True.
    """
    global _env
    if _env is None or no_cache:
        _env = collect_environment_without_packages()
        _env["packages"] = collect_loaded_packages()
    return _env


def collect_loaded_packages() -> List[Tuple[str, str]]:
    """
    Return the currently loaded package names and their versions.
    """
    dists = get_installed_distributions()
    get_dist_files = DistFilesFinder()
    file_table = {}
    for dist in dists:
        for file in get_dist_files(dist):
            file_table[file] = dist
    used_dists = set()
    # we greedily load all values to a list to avoid weird
    # "dictionary changed size during iteration" errors
    for module in list(sys.modules.values()):
        try:
            dist = file_table[module.__file__]
        except (AttributeError, KeyError):
            continue
        used_dists.add(dist)
    return sorted((dist.project_name, dist.version) for dist in used_dists)


class DistFilesFinder:
    """Functor to find the files belonging to a package."""

    def __init__(self):
        """Initialize a new DistFilesFinder."""
        try:
            self.sitedirs = set(site.getsitepackages() + [site.getusersitepackages()])
        except AttributeError:
            self.sitedirs = [get_python_lib()]

    def __call__(self, dist: Union["pip._vendor.pkg_resources.DistInfoDistribution",
                                   "pip._vendor.pkg_resources.EggInfoDistribution"]) \
            -> Iterable[str]:  # noqa: D401
        """
        Generator of the files belonging to a package.

        :param dist: The package object.
        """
        if dist.has_metadata("RECORD"):
            lines = dist.get_metadata_lines("RECORD")
            paths = [l.split(",")[0] for l in lines]
            for p in paths:
                yield os.path.abspath(os.path.join(dist.location, p))
            return
        if dist.has_metadata("installed-files.txt"):
            paths = dist.get_metadata_lines("installed-files.txt")
            for p in paths:
                yield os.path.abspath(os.path.join(dist.egg_info, p))
            return
        if dist.location in self.sitedirs:
            # egg-info without an explicit file list
            file_probe = os.path.join(dist.location, dist.project_name + ".py")
            if os.path.isfile(file_probe):
                yield os.path.abspath(file_probe)
                return
            for dir_probe in (os.path.join(dist.location, dist.project_name),
                              os.path.join(dist.location, dist.project_name.lower())):
                if os.path.isdir(dir_probe):
                    for root, _, files in os.walk(dir_probe):
                        for file in files:
                            yield os.path.abspath(os.path.join(root, file))
                    break
            return
        if dist.module_path is not None:
            # development install
            for root, _, files in os.walk(dist.module_path):
                for file in files:
                    yield os.path.abspath(os.path.join(root, file))
            return
        # we did our best and still failed at this point
