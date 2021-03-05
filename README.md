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

Or if you would like to build it yourself:

```
$ git clone git://github.com/devWhyqueue/plagdef
$ pip install -e .
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
````

# Publish to PyPI

In your virtual environment build and upload PlagDef:

```
$ python -m build
$ twine upload dist/*
````
