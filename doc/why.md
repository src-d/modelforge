# Why was Modelforge created?

There is a need for solution to manage trained machine learning models. It is not critical if the number
of models is low, of course, but problems are going to arise if it grows. Model version management
is required to track the development progress. Files must be synchronized. If you want to share
your trained models to the public, you require a presentation - a catalogue for discovery.
Finally, there is always the problem with reproducibility: a model should ideally define
the environment and the instructions to be re-generated.

ML engineers typically address those problems in one of the following ways:

1. Ignore them and live in chaos.
2. Pick any serialization format and dump everything somewhere as-is. Reproducibility and scalability
are ignored. Public sharing goes rough, it is impossible to transition from a model file to documentation.
3. Use Version Control Systems. Versioning is based on repository revisions. However, Git is not
optimal for managing large files, and ML models are often huge, so Git LFS is required and a separate
repository for each model. Given hundreds of different model types, this is not scalable.
4. Craft an ad-hoc in-house solution such as [TensorFlow Hub](https://tfhub.dev) or a database.
It most probably depends on the specific type of models and has to be updated manually.
Reproducibility is often out of scope.

Modelforge tries to be a universal platform which provides scalability, versioning, reproducibility
and ease of distribution. Yet it stays away from ML internals. From Modelforge's perspective, each
model is a black box which can be serialized and deserialized, nothing more. Read [Modelforge Model](model.md)
for details.
