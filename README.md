# Modelforge [![Build Status](https://travis-ci.org/src-d/modelforge.svg)](https://travis-ci.org/src-d/modelforge) [![codecov](https://codecov.io/github/src-d/modelforge/coverage.svg?branch=develop)](https://codecov.io/gh/src-d/modelforge) [![PyPI](https://img.shields.io/pypi/v/modelforge.svg)](https://pypi.python.org/pypi/modelforge)

This project is the foundation for sharing machine learning models. It helps to maintain the
*registry*, the remote storage where all model files are stored in a structured, cataloged way.
It defines `modelforge.Model`, the base class for all the models which is capable of automatic
fetching from the registry. It provides the abstraction over loading and saving models on disk
as well.

Each model receives a UUID and carries other metadata. The underlying file format is
[ASDF](https://github.com/spacetelescope/asdf).

Currently, only one registry storage backend is supported: Google Cloud Storage.

[src-d/ast2vec](https://github.com/src-d/ast2vec) uses `modelforge` to make ML on source code accessible
for everybody.

## Install

```
pip3 install modelforge
```

## Usage

The project exposes two interfaces: API and command line.

#### API

`modelforge` package contains the most important classes and functions: `Model` base class,
`merge_strings`, `split_strings` which optimize the serialization of string lists,
`disassemble_sparse_matrix`, `assemble_sparse_matrix` which handle sparse matrices.
A "model" here means something which holds the data and can be (de)serialized, like in
[web development](https://docs.djangoproject.com/en/2.0/topics/db/models/).

Models can be registered with `modelforge.register_model()`
- this is not strictly needed, but needed for extended model dumps. Most typically, you would like
to import all your model classes and register them in a single module.

It is possible to register a custom registry storage with `modelforge.backends.register_backend()`.

#### Command line

```
python3 -m modelforge --help
```

* `dump` prints brief information about the model. Local path, URL or UUID may be specified.
* `publish` pushes the model file to the registry and updates the index.
* `list` lists all the models in the registry.
* `init` initializes the empty registry.

#### Configuration

It is possible to specify the default backend, backend's options and the **vendor**. Create
`modelforgecfg.py` anywhere in your project tree.

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

## License

Apache 2.0.
