# Modelforge Model

**Model** is the core concept in Modelforge. A model consists of:

|                         field | description                                 | type   | required? |
|------------------------------:|:--------------------------------------------|:-------|:----------|
|                 [uuid](#uuid) | Unique identifier                           | [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) string | yes |
|                 [name](#name) | Type identifier                             | string | yes |
|             [series](#series) | Subtype identifier                          | string | yes |
|           [version](#version) | Version                                     | [semver](https://semver.org)-like list of 3 numbers or single number | yes |
|     [created_at](#created_at) | Date and time when model was generated      | datetime string | yes |
|             [parent](#parent) | Unique identifier of the previous version   | [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) string | yes |
|   [description](#description) | Information about the model                 | string | yes |
|             [source](#source) | Download link or file path                  | string | yes |
|                 [size](#size) | Size of the file                            | int    | yes |
|           [license](#license) | License of the model                        | [SPDX](https://spdx.org/licenses/) identifier or "Proprietary" string | yes |
|   [environment](#environment) | Description of the computing environment used to create the model | <see the details below> | yes |
| [dependencies](#dependencies) | Other models on which our model depend      | UUID strings mapped to Model-s | no |
|                 [code](#code) | Example of model usage in Python            | string | no |
|         [datasets](#datasets) | List of datasets used to generate the model | list of pairs \[name, URL\] | no |
|     [references](#references) | List of relevant resources                  | list of URLs | no |
|                 [tags](#tags) | List of categories for classification       | list of strings | no |
|           [metrics](#metrics) | Achieved quality metrics                    | mapping from names to numbers | no |
|               [extra](#extra) | Additional information which is not covered by any other fields | custom | no |

"Required" flag means whether the field always has a non-empty value.
The table from above defines "metadata" in Modelforge.
The data scheme of the actual payload of the model is referred to as the "internal format", and it is opaque.
It can be any tree-like data structure with string, numbers, lists, subtrees and tensors inside.

### uuid

Each model has a global unique identifier. It allows to reference any model in the registry.
Example: `dd6a841c-94e1-47f4-8029-b9aabb32505e`.

### name

Short name of the model family, the convention is dashed-lowercase. The name defines the *type*
of the model - it's internal format. For example, the models
which correspond to document frequencies (as in bag-of-words) are named "docfreq".

### series

Short name of the model series, the same convention as with [name](#name). For example,
the document frequencies calculated from an English Wikipedia dump in 2018 have "wiki-en-2018" series.

### version

It is always a good idea to follow [semver](https://semver.org) for versioning data:

1. In case of a breaking change in the internal format, we increment the major part.
2. In case of a serious quality improvement without breaking the internal format, we increment the minor part.
3. In other cases we increment the patch part.

There is an alternative, "no-brainer" versioning scheme which is followed by Chrome and Firefox: increment the only number.

### created_at

Date and time when the model was last saved on disk.

### parent

Unique identifier ([uuid](#uuid)) of the previous model. When a new version is issued, it points
to the old one.

### description

Markdown text which describes the model. It is a good idea to include the achieved quality metric values here.
However, machine-readable structured values should be put in [metrics](#metrics).

### source

Models are loaded either from disk or from a URL. This attribute contains the corresponding FS path
or the download link.

### size

Size of the model file.

### license

Models should always have an explicit usage license. Modelforge supports "Proprietary" value
and the identifiers from the [SPDX database](https://spdx.org/licenses/).

### environment

It is important to save as much information about the programming environment used to generate
the model, as possible. Modelforge contains:

* Running OS description, e.g. `Linux-4.15.0-39-generic-x86_64-with-Ubuntu-18.04-bionic`
* Python interpreter version, e.g. `3.7.1 (default, Oct 22 2018, 11:21:55) [GCC 8.2.0]`
* Installed packages which were loaded while the model was being saved, and their versions.

The format is `{"platform": "...", "python": "...", "packages": [["name", "version"],...]}`

### dependencies

Nested list of metadata belonging to the upstream models. Listing a model in `dependencies` means
that it is impossible to use the dependee without it. This should not be confused with
the data used to generate the model, which are listed in `datasets`.

### code

Code example of how to load the model and use it.

### datasets

List of the entities used to create the model. They can be real datasets or other models.

### references

List of relevant links for the model. It augments the description.

### tags

List of tags - categories for model classification.

### metrics

Achieved quality metric values, in dictionary format.

### extra

Any other information.
 