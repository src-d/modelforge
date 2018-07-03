# Modelforge [![Build Status](https://travis-ci.org/src-d/modelforge.svg)](https://travis-ci.org/src-d/modelforge) [![codecov](https://codecov.io/github/src-d/modelforge/coverage.svg?branch=develop)](https://codecov.io/gh/src-d/modelforge) [![PyPI](https://img.shields.io/pypi/v/modelforge.svg)](https://pypi.python.org/pypi/modelforge)

This project is the foundation for sharing machine learning models. It implements a git based
index to maintain the *registry*, the remote storage where all model files are stored in a 
structured, cataloged way. It defines `modelforge.Model`, the base class for all the models which 
is capable of automatic fetching from the registry. It provides the abstraction over managing 
models on disk as well.

Each model receives a UUID and carries other metadata. The underlying file format is
[ASDF](https://github.com/spacetelescope/asdf).

Currently, only one registry storage backend is supported: Google Cloud Storage. Our index is
stored at [src-d/models](https://github.com/src-d/models).

[src-d/ml](https://github.com/src-d/ml) uses `modelforge` to make ML on source code accessible
for everybody.


## Install

```
pip3 install modelforge
```


## Usage

The project exposes two interfaces: [API](doc/api.md) and [command line](doc/cmd.md).


#### Configuration

When using Modelforge, it is possible to store default values, whether you are using the package as
an API or with the command line. To do so, simply create a `modelforgecfg.py` anywhere in your 
project tree or directly in the `package`, and modify the following values to suit your needs:

```
VENDOR = "user"  # name of the issuing vendor for models
BACKEND = "gcs"  # type of backend to use
BACKEND_ARGS = "bucket='user_bucket.models',credentials='key.json'"  # all backend arguments 
INDEX_REPO = "https://github.com/user/models"  # git repo for the index
CACHE_DIR = "~/.cache/modelforge"  # default cache to use for the index
ALWAYS_SIGNOFF = True  # whether to add a DCO line on each commit message
```


#### Docker image

```
docker build -t srcd/modelforge .
docker run -it --rm srcd/modelforge --help
```


## Contributions
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

We use [PEP8](https://www.python.org/dev/peps/pep-0008/) with line length 99 and ". All the tests
must pass:

```
python3 -m unittest discover /path/to/modelforge
```

If you wish to make your model available in [src-d/models](https://github.com/src-d/models), please 
clone the repository and use the `publish` command to upload your model on your fork, then, simply 
open a PR. If you are using your own backend, don't forget to add read access to everybody. If you
wish to publish the model our GCS bucket, feel free to open an issue to contact us.

## License

Apache 2.0.
