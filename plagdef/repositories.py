from __future__ import annotations

import logging
from ast import literal_eval
from configparser import ConfigParser
from itertools import islice
from pathlib import Path

import magic
import pdfplumber
from magic import MagicException
from tqdm.contrib.concurrent import thread_map

from plagdef.model.models import Document

log = logging.getLogger(__name__)


class DocumentFileRepository:
    def __init__(self, dir_path: Path, lang: str, recursive=False, at_least_two=True):
        self.lang = lang
        self._dir_path = dir_path
        self._recursive = recursive
        if not dir_path.is_dir():
            raise NotADirectoryError(f'The given path {dir_path} does not point to an existing directory!')
        if at_least_two and (not any(self._list_files()) or not next(islice(self._list_files(), 1, None), None)):
            raise NoDocumentFilePairFoundError(f'The directory {dir_path} must contain at least two documents.')

    def _list_files(self):
        if self._recursive:
            return (file_path for file_path in self._dir_path.rglob('*') if file_path.is_file())
        else:
            return (file_path for file_path in self._dir_path.iterdir() if file_path.is_file())

    def list(self) -> set[Document]:
        files = list(self._list_files())
        docs = thread_map(self._read_file, files, desc=f"Reading documents in '{self._dir_path}'",
                          unit='doc', total=len(files))
        return set(filter(None, docs))

    def _read_file(self, file):
        if file.suffix == '.pdf':
            with pdfplumber.open(file) as pdf:
                text = ' '.join(filter(None, (page.extract_text() for page in pdf.pages)))
                return Document(file.stem, str(text))
        else:
            try:
                detect_enc = magic.Magic(mime_encoding=True)
                enc = detect_enc.from_buffer(open(str(file), 'rb').read(2048))
                text = file.read_text(encoding=enc)
                return Document(file.stem, str(text))
            except (UnicodeDecodeError, LookupError, MagicException):
                log.error(f"The file '{file.name}' has an unsupported encoding and cannot be read.")
                log.debug('Following error occurred:', exc_info=True)


class DocumentPairReportFileRepository:
    def __init__(self, out_path: Path):
        if not out_path.is_dir():
            raise NotADirectoryError(f'The given path {out_path} does not point to an existing directory!')
        self._out_path = out_path

    def add(self, doc_pair_report):
        file_name = Path(f'{doc_pair_report.doc1.name}-{doc_pair_report.doc2.name}.{doc_pair_report.format}')
        file_path = self._out_path / file_name
        with file_path.open('w', encoding='utf-8') as f:
            f.write(doc_pair_report.content)


class ConfigFileRepository:
    def __init__(self, config_path: Path):
        if not config_path.is_file():
            raise FileNotFoundError(f'The given path {config_path} does not point to an existing file!')
        if not config_path.suffix == '.ini':
            raise UnsupportedFileFormatError(f'The config file format must be INI.')
        self.config_path = config_path

    def get(self) -> dict:
        parser = ConfigParser()
        parser.read(self.config_path)
        config = {}
        for section in parser.sections():
            typed_config = [(key, literal_eval(val)) for key, val in parser.items(section)]
            config.update(dict(typed_config))
        return config


class NoDocumentFilePairFoundError(Exception):
    pass


class UnsupportedFileFormatError(Exception):
    pass
