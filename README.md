# PlagDef

[![PyPI version](https://badge.fury.io/py/plagdef.svg)](https://badge.fury.io/py/plagdef)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/plagdef)
![GitHub](https://img.shields.io/github/license/devWhyqueue/plagdef)
[![Build Status](https://travis-ci.com/devWhyqueue/plagdef.svg?branch=main)](https://travis-ci.com/devWhyqueue/plagdef)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=devWhyqueue_plagdef&metric=coverage)](https://sonarcloud.io/dashboard?id=devWhyqueue_plagdef)

PlagDef supports plagiarism detection for student assignments.

# Installation

Get it from PyPI:

```
$ pip install plagdef
````

Or build it yourself:

```
$ git clone git://github.com/devWhyqueue/plagdef
$ pip install -e .
````

And install necessary resources:

```
$ python -m nltk.downloader punkt
$ python -m spacy download en_core_web_trf
$ python -m spacy download de_dep_news_trf
````

# Usage

Run the CLI and show help:

```
$ plagdef -h
````

# Development

Clone the repo and install dependencies/resources:

```
$ git clone git://github.com/devWhyqueue/plagdef
$ pipenv install --dev
$ pipenv run python -m nltk.downloader punkt
$ pipenv run python -m spacy download en_core_web_trf
$ pipenv run python -m spacy download de_dep_news_trf
````

# Publish to PyPI

In your virtual environment build and upload PlagDef:

```
$ python -m build
$ twine upload dist/*
````
