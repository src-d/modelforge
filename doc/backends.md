# Backends

Modelforge models must live in a place which is accessible from all over the world.
There is a backend mechanism that abstracts getting model files from
and putting them to the cloud. Each backend must satisfy the following
interface:

* Initialize the storage. Optionally, remove all existing files.
* Upload a file.
* Download a file.
* Delete a file.

So far, only one backend is written: Google Cloud Storage.

### Google Cloud Storage

GCS backend requires a dedicated bucket which is managed monopolously.
It makes the model files publicly accessible through HTTP, so that they are
trivial for everybody to download. It requires suitable GCS credentials
(JSON) to initialize, and to upload or delete models.

GCS backend organizes the bucket in tree-like structure:

1. The first level is always `"models"`
2. The second level is model types (`"name"`).
3. The third level is models' unique identifiers - `"uuid"`.

For example, this is a valid GCS path: `models/docfreq/dd6a841c-94e1-47f4-8029-b9aabb32505e.asdf`.
