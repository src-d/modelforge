# Model storage format

Modelforge models serialize to [Advanced Scientific Data Format](https://blog.sourced.tech/post/asdf/).
[Metadata](model.md) is placed under `"meta"` branch in the ASDF tree, and the internal format data
goes directly to the top level.

ASDF takes care of JSON-like structures and of numpy arrays. It cannot automatically handle
classes, so it's the developer responsibility to convert such objects to "JSON with tensors".
Besides, some regular Python objects should be converted to numpy arrays, because ASDF deals with them
very efficiently: it supports [mmap()](https://en.wikipedia.org/wiki/Memory-mapped_file) which avoids
materializing large arrays in memory, and it also supports transparent compression with zlib, bzip2 or
[lz4](https://en.wikipedia.org/wiki/LZ4_(compression_algorithm)).
Modelforge always compresses arrays with lz4, unless they are explicitly listed as not compressible.