# Configuration

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