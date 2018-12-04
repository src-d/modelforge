# Model storage format

Modelforge models serialize to [Advanced Scientific Data Format](https://blog.sourced.tech/post/asdf/).
[Metadata](model.md) is placed under `"meta"` branch in the ASDF tree, and the internal format data
goes directly to the top level.

ASDF takes care of JSON-like structures and of numpy arrays. It cannot automatically handle
classes, so it's the developer responsibility to convert such objects to "JSON with tensors".
Besides, some regular Python objects should be converted to numpy arrays, because ASDF deals with them
very efficiently: it supports [mmap()](https://en.wikipedia.org/wiki/Memory-mapped_file) which avoids
materializing large arrays in memory, and it also supports transparent compression with zlib, bzip2 or
[lz4](https://en.wikipedia.org/wiki/LZ4_\(compression_algorithm\)).
Modelforge always compresses arrays with lz4, unless they are explicitly listed as not compressible.

### Example of Python -> numpy conversion benefit

Suppose that your model is Document Frequencies: it maps each word from
your vocabulary to an integer number which indicates how many times that
word appeared in structural parts of the dataset. Let's take
[Yelp Dataset](https://www.kaggle.com/yelp-dataset/yelp-dataset) with reviews,
tokenize with [Spacy](), calculate document frequencies and pick 10,000
most frequent words.

```python
from collections import defaultdict
import io
import json
import zipfile

import spacy
from tqdm import tqdm

# https://www.kaggle.com/yelp-dataset/yelp-dataset/downloads/yelp-dataset.zip
docfreq = defaultdict(int)
nlp = spacy.load("en", disable=["tagger", "parser", "ner", "textcat"])
max_reviews = 1000000
with zipfile.ZipFile("yelp-dataset.zip") as zf:
    with zf.open("yelp_academic_dataset_review.json") as rf:
        for i, line in tqdm(enumerate(io.TextIOWrapper(rf)), total=max_reviews):
            for token in nlp(json.loads(line)["text"]):
                if not token.is_stop and token.is_alpha:
                    docfreq[token.lemma_] += 1
            if (i + 1) == max_reviews:
                break
docfreq = {k: v for v, k in sorted([(v, k) for k, v in docfreq.items()],
                                   reverse=True)[:10000]}
```

Let's compare the sizes of pickle-s and asdf-s with various preprocessing.

```python
import pickle

with open("/tmp/docfreq.pickle", "wb") as fout:
    pickle.dump(docfreq, fout, protocol=4)

import lz4.frame
with open("/tmp/docfreq.pickle.lz4", "wb") as fout:
    fout.write(lz4.frame.compress(pickle.dumps(docfreq, protocol=4)))

import asdf

asdf.AsdfFile(tree={"docfreq": docfreq}).write_to("/tmp/docfreq_raw.asdf")

from modelforge import merge_strings, squeeze_bits
import numpy

def write_docfreq(words, freqs, path, compression="lz4"):
    asdf.AsdfFile(tree={"docfreq": {
        "words": merge_strings(words),
        "freqs": squeeze_bits(freqs)
    }}).write_to(path, all_array_compression=compression)

words = list(docfreq.keys())
freqs = numpy.array(list(docfreq.values()))
write_docfreq(words, freqs, "/tmp/docfreq_array.asdf", compression=None)
write_docfreq(words, freqs, "/tmp/docfreq_array_lz4.asdf")

words = sorted(docfreq.keys())
freqs = numpy.array([docfreq[k] for k in words])
write_docfreq(words, freqs, "/tmp/docfreq_array_sorted_keys_lz4.asdf")

pairs = sorted([(v, k) for k, v in docfreq.items()], reverse=True)
words = [k for v, k in pairs]
freqs = numpy.array([v for v, k in pairs])
write_docfreq(words, freqs, "/tmp/docfreq_array_sorted_values_lz4.asdf")

pairs = sorted([(v, k) for k, v in docfreq.items()])
words = [k for v, k in pairs]
freqs = numpy.diff(numpy.array([v for v, k in pairs]))
write_docfreq(words, freqs, "/tmp/docfreq_array_sorted_values_diff_lz4.asdf")

with open("/tmp/docfreq_sort_diff.pickle.lz4", "wb") as fout:
    fout.write(lz4.frame.compress(pickle.dumps(
        (merge_strings(words), squeeze_bits(freqs)), protocol=4)))

import os

def size(path):
    return os.stat(path).st_size

print(size("/tmp/docfreq.pickle"),
      size("/tmp/docfreq.pickle.lz4"),
      size("/tmp/docfreq_sort_diff.pickle.lz4"),
      size("/tmp/docfreq_raw.asdf"),
      size("/tmp/docfreq_array.asdf"),
      size("/tmp/docfreq_array_lz4.asdf"),
      size("/tmp/docfreq_array_sorted_keys_lz4.asdf"),
      size("/tmp/docfreq_array_sorted_values_lz4.asdf"),
      size("/tmp/docfreq_array_sorted_values_diff_lz4.asdf"))
```

You should see numbers similar to these:

| method                                   | size (smaller is better) |
|-----------------------------------------:|:-------------------------|
| pickle                                   | 121583 |
| pickle + lz4                             | 110172 |
| pickle + sort(value) + diff + lz4        | 77436  |
| asdf                                     | 141515 |
| asdf + arrays                            | 114075 |
| asdf + arrays + lz4                      | 79455  |
| asdf + arrays + sort(key) + lz4          | 78596  |
| asdf + arrays + sort(value) + lz4        | 68812  |
| asdf + arrays + sort(value) + diff + lz4 | 58513  |

ASDF has [many advantages over the other formats](https://blog.sourced.tech/post/asdf/),
and it is clearly superior to pickle-s in particular.

This example shows some tricks how to preprocess data to achieve better compression ratios.
The list of strings should be merged into a giant string, and the order
should be in increasing frequency order. That giant string maps to a numpy array
and compressed, and an increasing integer sequence can be also compressed
efficiently after differentiation. Differentiation is a lossless operation
and the original sequence can be easily restored using `numpy.cumsum`.

Here we are using some helper functions from `modelforge` package to merge
several strings together and to lower the bitness of an integer array if
possible.

### Advice on achieving good compression ratios

1. If you have many strings belonging to the same object (as in the example above),
merge them together using `modelforge.merge_strings()`. The original sequence
can be restored using `modelforge.split_strings()`.
2. It is always a good idea to sort your data: strings, numbers, etc.
This way similar values appear near each other and windowed lz4 does a better job.
If you need to maintain a specific order, adding an additional array with
indexes may or may not overweigh the benefits.
3. If you sort an array of numbers, consider differentiation. This way
you have a chance of getting many zeros or otherwise constant numbers in a row
and lz4 compresses them well.
4. If you have an unsigned integer array with a low upper bound, consider
passing it through `modelforge.squeeze_bits()`. This way uint32 can be
converted to uint16 or even uint8 without any precision loss.
5. Usually you don't need float64. Ensure float32 dtype instead.
6. If you expect high entropy in an array, don't compress it: lz4 is too
basic to perform well in this case, and you will also speed up deserialization.

### Sparse arrays

Sparse arrays (`scipy.sparse.*_matrix`) are Python classes and thus
cannot be serialized by ASDF automatically. There are
`modelforge.disassemble_sparse_matrix` and `modelforge.assemble_sparse_matrix`
functions which solve this problem.