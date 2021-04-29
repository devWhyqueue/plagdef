from __future__ import annotations

import logging
import os
from ast import literal_eval
from collections import Counter
from configparser import ConfigParser
from copy import deepcopy
from json import JSONDecodeError
from pathlib import Path
from pickle import dump, load, UnpicklingError
from unicodedata import normalize

import jsonpickle
import magic
import pdfplumber
from magic import MagicException
from sortedcontainers import SortedSet
from tqdm.contrib.concurrent import thread_map

from plagdef.model import models

log = logging.getLogger(__name__)
jsonpickle.set_encoder_options('json', indent=4)


class DocumentFileRepository:
    def __init__(self, dir_path: Path, lang: str, recursive=False):
        self.lang = lang
        self.dir_path = dir_path
        self._recursive = recursive
        if not dir_path.is_dir():
            raise NotADirectoryError(f'The given path {dir_path} does not point to an existing directory!')

    def _list_files(self):
        if self._recursive:
            return (file for file in self.dir_path.rglob('*') if file.is_file() and file.suffix != '.pdef')
        else:
            return (file for file in self.dir_path.iterdir() if file.is_file() and file.suffix != '.pdef')

    def list(self) -> set[models.Document]:
        files = list(self._list_files())
        docs = thread_map(self._read_file, files, desc=f"Reading documents in '{self.dir_path}'",
                          unit='doc', total=len(files), max_workers=os.cpu_count())
        return set(filter(None, docs))

    def _read_file(self, file):
        if file.suffix == '.pdf':
            with pdfplumber.open(file) as pdf:
                text = ' '.join(filter(None, (page.extract_text() for page in pdf.pages)))
                normalized_text = normalize('NFC', text)
                return models.Document(file.stem, str(file.resolve()), normalized_text)
        else:
            try:
                detect_enc = magic.Magic(mime_encoding=True)
                enc = detect_enc.from_buffer(open(str(file), 'rb').read(2048))
                enc_str = enc if enc != 'utf-8' else 'utf-8-sig'
                text = file.read_text(encoding=enc_str)
                normalized_text = normalize('NFC', text)
                return models.Document(file.stem, str(file.resolve()), normalized_text)
            except (UnicodeDecodeError, LookupError, MagicException):
                log.error(f"The file '{file.name}' has an unsupported encoding and cannot be read.")
                log.debug('Following error occurred:', exc_info=True)


class DocumentPairMatchesJsonRepository:
    def __init__(self, out_path: Path):
        if not out_path.is_dir():
            raise NotADirectoryError(f"The given path '{out_path}' does not point to an existing directory!")
        self._out_path = out_path

    def save(self, doc_pair_matches):
        clone = deepcopy(doc_pair_matches)
        clone.doc1.vocab, clone.doc2.vocab = Counter(), Counter()
        clone.doc1._sents, clone.doc2._sents = SortedSet(), SortedSet()
        file_name = Path(f'{clone.doc1.name}-{clone.doc2.name}.json')
        file_path = self._out_path / file_name
        with file_path.open('w', encoding='utf-8') as f:
            text = jsonpickle.encode(clone)
            f.write(text)

    def list(self) -> set[models.DocumentPairMatches]:
        doc_pair_matches_list = set()
        for file in self._out_path.iterdir():
            if file.is_file() and file.suffix == '.json':
                try:
                    text = file.read_text(encoding='utf-8')
                    doc_pair_matches = jsonpickle.decode(text)
                    doc_pair_matches_list.add(doc_pair_matches)
                except (UnicodeDecodeError, JSONDecodeError):
                    log.error(f"The file '{file.name}' could not be read.")
                    log.debug('Following error occurred:', exc_info=True)
        return doc_pair_matches_list


class ConfigFileRepository:
    def __init__(self, config_path: Path):
        if not config_path.is_file():
            raise FileNotFoundError(f'The given path {config_path} does not point to an existing file!')
        if not config_path.suffix == '.ini':
            raise UnsupportedFileFormatError(f'The config file format must be INI.')
        self.config_path = config_path
        self._custom_config = {}

    def get(self) -> dict:
        parser = ConfigParser()
        parser.read(self.config_path)
        config = {}
        for section in parser.sections():
            typed_config = [(key, literal_eval(val)) for key, val in parser.items(section)]
            config.update(dict(typed_config))
        return {**config, **self._custom_config}

    def update(self, config: dict):
        self._custom_config = config


class DocumentPickleRepository:
    FILE_NAME = '_prep_docs.pdef'

    def __init__(self, dir_path: Path):
        if not dir_path.is_dir():
            raise NotADirectoryError(f"The given path '{dir_path}' does not point to an existing directory!")
        self.file_path = dir_path / DocumentPickleRepository.FILE_NAME

    def save(self, docs: set[models.Document]):
        with self.file_path.open('wb') as file:
            dump(docs, file)

    def list(self) -> set[models.Document]:
        if self.file_path.exists():
            log.info('Found preprocessing file. Deserializing...')
            try:
                with self.file_path.open('rb') as file:
                    return load(file)
            except (UnpicklingError, EOFError):
                log.warning(f"Could not deserialize preprocessing file, '{self.file_path.name}' seems to be corrupted.")
                log.debug('Following error occurred:', exc_info=True)
        return set()


class UnsupportedFileFormatError(Exception):
    pass
