# API usage

Modelforge is meant to help developers and researchers share machine learning models 
**of any kind**, that is to say it is agnostic of the framework used to obtain it. This sections 
covers the abstraction's implemented here, and how you can extend them for you own usage. All the
managing can be done through the command line and is documented [here](cmd.md).


## Models

A "model" here means something which holds the data and can be (de)serialized, like in
[web development](https://docs.djangoproject.com/en/2.0/topics/db/models/). We chose the
[asdf format](https://asdf.readthedocs.io/en/latest/) to store the models.

The `Model` class in `model.py` is the base class to use if you wish to create a new model. These
are the methods that must be defined for your custom class to be compatible:

- `_load_tree`: should load the model from the `tree` argument, a dict holding all the data
- `_generate_tree`: should generate the `tree`, a dict holding all the data needed to load the 
model
- `dump`: should return a string containing information about the model

You will also need to override the base class's static attributes: 

- `NAME`: to differentiate each model type
- `VENDOR`: to keep track of the ownership status of each model

We use the `NAME` as well as a [UUID](https://fr.wikipedia.org/wiki/Universal_Unique_Identifier) 
attributed to each model instance in order to index models pushed to a registry in an orderly 
fashion. Docker images work roughly the same way, the UUID replacing the sha256 signature, and 
similarly for any given model type present in an index there is a "default" model, which 
corresponds to a "latest" docker image. However we also provide additional building blocks for
versioning: the `derive` method can be used to create a new model with an incremented version, a
new UUID, and whose `parent` metadata field will be linked to the old model. This can be useful in
a wide range of cases, e.g. if you are training an ML model and wish to save it every n iteration.

You may want to add some custom methods, e.g. `predict`. To see some examples, checkout our models 
in [src-d/ml](https://github.com/src-d/ml/tree/master/sourced/ml/models), and try them out by 
downloading them from [src-d/models](https://github.com/src-d/models).

We have also implemented some useful functions for large scale models:
- `merge_strings` and `split_strings`, which optimize the serialization of string lists,
- `assemble_sparse_matrix` and `disassemble_sparse_matrix`, which handle sparse scipy matrices.


Models can be registered with `modelforge.register_model()` - this is not strictly required, but 
needed for extended model dumps. Most typically, you would like to import all your model classes 
and register them in a single module, like [here](https://github.com/src-d/ml/blob/master/sourced/ml/models/__init__.py).


## Backends 

Although we have implemented GCS backend for our own usage, we have made it possible for 
`modelforge` to be used with custom backends. To do so, one would simply need to create a class
inheriting from the `StorageBackend` class in `storage_backend.py`, and define the following 
methods:

- `reset(self, force: bool)`: should initialize the backend. An error should be raised if `force` 
has not been specified, and the backend already exists.
- `fetch_model(self, source: str, file: str)`: should download the model from `source` and store it
 at `file`.  
- `upload_model(self, path: str, meta: dict, force: bool)`: should upload the model in `path`, 
using the `meta` dictionary containing the model type and UUID. An error should be raised if 
`force` has not been specified, and a model of the same type and UUID is already uploaded. 
- `delete_model(self, meta: dict)`: should delete the model from the backend, using the `meta` 
dictionary containing the model type and UUID.

Then, register your backend using the `register_backend` function in `backends.py`. 

For an example of how this can be done, check out `gcs_backend.py`.
