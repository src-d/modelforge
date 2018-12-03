# Modelforge [![docs on gitbook](https://img.shields.io/badge/docs-gitbook-brightgreen.svg)](https://docs.sourced.tech/modelforge/) [![Build Status](https://travis-ci.org/src-d/modelforge.svg)](https://travis-ci.org/src-d/modelforge) [![codecov](https://codecov.io/github/src-d/modelforge/coverage.svg)](https://codecov.io/gh/src-d/modelforge) [![PyPI](https://img.shields.io/pypi/v/modelforge.svg)](https://pypi.python.org/pypi/modelforge)

Modelforge is a foundation for sharing trained machine learning models. It is a set of command line
tools and a Python library. Modelforge maintains model files in a third-party remote storage service
("cloud") using the backend mechanism. Model metadata (download links, names, descriptions, versions,
etc.) resides in a Git repository called the "Index", and documentation is automatically generated
there. Modelforge does no assumptions about the models: they can be of any origin, such as TensorFlow,
scikit-learn, or your custom. The underlying model storage format -
[Advanced Scientific Data Format](https://github.com/spacetelescope/asdf) - can wrap any data
easily and efficiently, but it's the developer's responsibility to convert.

Learn more about:

* [Why?](doc/why.md) - what problem Modelforge tries to solve.
* [Modelforge model](doc/model.md) - what is a model in Modelforge context.
* [Model storage format](doc/model_storage_format.md) - low-level serialization details.
* [Backends](doc/backends.md) - extension system to upload and download models from clouds.
* [Git Index](doc/git_index.md) - how documentation about the models is generated from the structured metadata.
* [Command line tools](doc/cmdline.md) - how to perform typical operations.
* [API](doc/api.md) - Modelforge API for developers.

#### Who uses Modelforge?

* source{d}, in [src-d/ml](https://github.com/src-d/ml) and [src-d/lookout-sdk-ml](https://github.com/src-d/lookout-sdk-ml); the public index is [src-d/models](https://github.com/src-d/models).

## Install

You can run Modelforge through Docker:
```
docker run -it --rm srcd/modelforge --help
```

or install it using the [Python package manager](https://github.com/pypa/pip):

```
pip3 install modelforge
```

## Usage

The project exposes two interfaces: [command line](doc/cmdline.md) and [API](doc/api.md).

## Contributions
Contributions are pretty much welcome! Please follow the [contributions guide](doc/contributing.md)
and the [code of conduct](doc/code_of_conduct.md).

If you wish to make your MLonCode model available in [src-d/models](https://github.com/src-d/models),
please  fork that repository and run `modelforge publish` to upload your model on your fork. Then
create a pull request. You should provide read access to the model file for everybody. If you
consider using our Google Cloud Storage bucket, feel free to contact us through GitHub issues.

## License

[Apache 2.0](LICENSE).
