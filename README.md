# PlagDef

[![PyPI version](https://badge.fury.io/py/plagdef.svg)](https://badge.fury.io/py/plagdef)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/plagdef)
![GitHub](https://img.shields.io/github/license/devWhyqueue/plagdef)
[![Test](https://github.com/devWhyqueue/plagdef/actions/workflows/test.yml/badge.svg)](https://github.com/devWhyqueue/plagdef/actions/workflows/test.yml)
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
$ python -m pip install -e .
````

# Requirements

## Tesseract

For OCR on PDF files you need Tesseract.\
To install Tesseract for your operating system take a look at:\
https://github.com/tesseract-ocr/tessdoc#500x

And don't forget to download the German language pack to your _tessdata_ folder from here:\
https://github.com/tesseract-ocr/tessdata

## Poppler

Poppler helps converting PDFs to images for Tesseract.\
Releases for Windows can be found here:\
https://github.com/oschwartz10612/poppler-windows/releases \
After the installation add the _bin_ folder to your PATH.

On Mac OS you can install Poppler via Homebrew:

```
$ brew install poppler
````

Linux users usually don't have to worry about Poppler because its preinstalled.\
If it's missing, however, refer to your package manager to install `poppler-utils`.

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
$ pipenv install --dev
````

# Publish to PyPI

In your virtual environment build and upload PlagDef:

```
$ python -m build
$ twine upload dist/*
````
