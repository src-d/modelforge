from setuptools import setup, find_packages
import sys

if sys.version_info < (3, 5, 0):
    typing = ["typing"]
else:
    typing = []


setup(
    name="modelforge",
    description='APIs and tools to work with abstract "models" - files '
                'with numpy arrays and metadata. It is possible to publish '
                'models, list them. There is a built-in cache. Storage has backends.',
    version="0.1.0-alpha",
    license="Apache 2.0",
    author="source{d}",
    author_email="machine-learning@sourced.tech",
    url="https://github.com/src-d/modelforge",
    download_url="https://github.com/src-d/modelforge",
    packages=find_packages(exclude=("modelforge.tests",)),
    keywords=["model", "asdf", "gcs", "google cloud storage",
              "machine learning"],
    install_requires=["asdf>=1.2,<2.0",
                      "lz4>=0.10.1",
                      "numpy>=1.12,<2.0",
                      "scipy>=0.17,<1.0",
                      "clint>=0.5.0",
                      "google-cloud-storage>=1.0,<2.0",
                      "python-dateutil"] + typing,
    package_data={"": ["LICENSE", "README.md"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries"
    ]
)
