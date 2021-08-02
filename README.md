# PlagDef

[![PyPI version](https://badge.fury.io/py/plagdef.svg)](https://badge.fury.io/py/plagdef)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/plagdef)
![GitHub](https://img.shields.io/github/license/devWhyqueue/plagdef)
[![Test](https://github.com/devWhyqueue/plagdef/actions/workflows/cd.yml/badge.svg)](https://github.com/devWhyqueue/plagdef/actions/workflows/test.yml)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=devWhyqueue_plagdef&metric=coverage)](https://sonarcloud.io/dashboard?id=devWhyqueue_plagdef)

A tool which makes life hard for students who try to make theirs simple.

# Installation

Get it from PyPI:

```
$ pip install plagdef
````

Or build it yourself:

```
$ git clone git://github.com/devWhyqueue/plagdef
$ poetry build
$ pip install dist/plagdef-{VERSION}.tar.gz
````

# Requirements

## OCRMyPDF

This library is used for improved PDF text extraction.\
To install its necessary dependencies for your operating system take a look at:\
https://ocrmypdf.readthedocs.io/en/latest/installation.html

And don't forget to download the German language pack to your _tessdata_ folder from here:\
https://github.com/tesseract-ocr/tessdata

## Libmagic

**After** (important!) you installed PlagDef, install the libmagic library.\
PlagDef uses it to detect character encodings.\
Further instructions can be found here:\
https://github.com/ahupp/python-magic#installation

# Usage

Run the GUI:

```
$ plagdef-gui
````

Or if you prefer a CLI:

```
$ plagdef -h
````

# Development

Clone the repo and install dependencies:

```
$ git clone git://github.com/devWhyqueue/plagdef
$ poetry install
````

# Publish to PyPI

In your virtual environment build and upload PlagDef:

```
$ poetry publish --build
````
