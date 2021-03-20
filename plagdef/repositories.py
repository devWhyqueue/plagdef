from __future__ import annotations

from ast import literal_eval
from configparser import ConfigParser
from itertools import islice
from os import listdir
from os.path import join, isfile
from pathlib import Path

from plagdef.model.legacy.algorithm import Document


class DocumentFileRepository:
    def __init__(self, dir_path: Path, lang: str):
        self.lang = lang
        if not dir_path.is_dir():
            raise NotADirectoryError(f'The given path {dir_path} does not point to an existing directory!')
        if not any(dir_path.iterdir()) or not next(islice(dir_path.iterdir(), 1, None), None):
            raise NoDocumentFilePairFoundError(f'The directory {dir_path} must contain at least two documents.')
        doc_files = [Path(join(dir_path, f)) for f in listdir(dir_path) if isfile(join(dir_path, f))]
        try:
            self._documents = [Document(f.stem, f.read_text()) for f in doc_files]
        except UnicodeDecodeError as e:
            raise UnsupportedFileFormatError(f'The directory {dir_path} contains files in an unsupported format.') \
                from e

    def list(self) -> [Document]:
        return self._documents


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
