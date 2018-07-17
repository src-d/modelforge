# Command line usage

In this section we cover in detail each of the commands implemented in Modelforge. Some of the 
commands share arguments (for the backend, git based index and jinja2 templates), they are 
described once at the bottom of this document.


```
modelforge --help
```

## Initializing the registry

With this command you can either initialize an empty registry, or delete all of the contents of a 
non-empty one and initialize it afterward. The git based index will also be cleared.

- `-f` / `--force`: To delete the existing registry if there is one.
- Backend arguments.
- Index arguments.


Example:

```
modelforge init --username user --password pass --index-repo https://github.com/user/models 
    --cache path/to/cache --force --backend "gcs" 
    --args bucket="user_bucket.models",credentials="path/to/key.json"
```

## Adding a model

With this command you can add a model to the registry.

- First (and only) positional argument: path to the model to publish.
- `--meta`: Path to a JSON containing the metadata of the model, use the `template_meta.json` file 
to create it. The non-nested `code` and `description`keys are for the default of the model type, if
is isn't not updated it will have no effect. Do not remove the `%s` in either of the `code, it is 
linked to the model's uuid/model_type. Any additional field can be added using the `extra`key. 
- `-d`/ `-update-defaults`: To set this model as the default for this model type. If the model is 
the first of his kind, it will become the default in all cases.
- `-f` / `--force`: To overwrite an existing model with the same type and UUID.
- Backend arguments.
- Index arguments.
- Template arguments.


Example:

```
modelforge publish path/to/my/model --username user --password pass  --cache path/to/cache 
    --backend "gcs" --args bucket="user_bucket.models",credentials="path/to/key.json"
    --index-repo https://github.com/user/models 
```

## Deleting a model

With this command you can delete a model from the registry.

- First (and only) positional argument: UUID of the model to delete.
- Backend arguments.
- Index arguments.
- Template arguments.


Example:

```
modelforge delete c70a7514-9257-4b33-b468-27a8588d4dfa --username user --password pass
    --backend "gcs" --args bucket="user_bucket.models",credentials="path/to/key.json"
    --index-repo https://github.com/user/models --cache path/to/cache 
```

## Listing all models

With this command you can list all the models in the registry, for each model type the default is 
tagged with a _*_.

- Index arguments.


Example:

```
modelforge list --username user --password pass --index-repo https://github.com/user/models 
    --cache path/to/cache 
```
  
## Dump information about a model

With this command you can get a dump of information concerning a specific model. The output of this
command depends completely on the `dump` method of the model's class. Naturally, if the model is 
stored in your filesystem there is no need to specify backend or index arguments.

- First (and only) positional argument: Path (if the model is stored on your filesystem), UUID or 
URL of the model. 
- Backend arguments.
- Index arguments.


Example:

```
modelforge dump c70a7514-9257-4b33-b468-27a8588d4dfa --username user --password pass
    --backend "gcs" --args bucket="user_bucket.models",credentials="path/to/key.json"
    --index-repo https://github.com/user/models --cache path/to/cache 
```

## Shared arguments

### Backend arguments

- `--backend`: The type of backend to use, at the moment only GCS is supported. For more 
information on how to add custom backends, check out our [API documentation](api.md).
- `--args`: All additional arguments required by the backend, formatted the following way:
`key1="value1",key2="value2",...`.

You can bypass rewriting these args each time by setting either `MODELFORGE_BACKEND` and 
`MODELFORGE_BACKEND_ARGS` as environment variables, or `BACKEND` and `BACKEND_ARGS` as constants in
the `modelforgecfg.py` file of your project.

In the case of a GCS backend you must only specify the bucket's name, as well as a path to the JSON
containing your private key if you are running the `init`, `publish` or `delete` command. 


### Index arguments

- `--cache`: Path to the cache where a copy of the git based index will be stored, defaults to 
`~/.cache`.
- `-s`/`--signoff`: Whether to add a [DCO](http://developercertificate.org/) to your commit 
message, if the registry is modified.

__TCP/HTTPS:__

Like for the backend credentials are required only if you are running the `init`, `publish` or 
`delete` command.  

- `--index-repo`: The URL to the repo where the index is: `http(s)://domain/path/to/repo` 
or `git://domain/path/to/repo`.
- `--username`: Your username on the git platform where the index is.
- `--password`: Your password on the git platform where the index is.


__SSH:__

To use this, you **must** have configured your SSH previously.

--index-repo: The URL to the repo where the index is: `(git+)ssh://git@domain/path/to/repo`.


You can also bypass rewriting these args each time by setting either `MODELFORGE_CACHE_DIR` and 
`MODELFORGE_INDEX_REPO` as environment variables or `CACHE_DIR` and `INDEX_REPO` as constants in 
the `modelforgecfg.py` file of your project, however if you are not using SSH you will need to 
specify your username and password in all cases. 


### Template arguments

If you wish to customize `.md` files of the git based index you can create alternated `.md.jinja2`
templates and use them here. You can check out what the default templates look like at 
[src-d/models](https://github.com/src-d/models). 

- `--template-model`: Path to the custom jinja2 template used for the `model.md` file stored in
the index, the `template_model.md.jinja2` file will be used if not specified. This is only used by
the `publish` command.
- `--template-readme`: Path to the custom jinja2 template used for the `readme.md` file stored in
the index, the `template_readme.md.jinja2` file will be used if not specified.
