from __future__ import annotations

import logging
import os
import re
from collections import Counter
from copy import deepcopy
from hashlib import blake2b
from io import BytesIO
from json import JSONDecodeError
from multiprocessing import Lock
from pathlib import Path
from pickle import dump, load, UnpicklingError
from unicodedata import normalize

import jsonpickle
import magic
import pdfplumber
from dependency_injector.wiring import Provide, inject, as_
from magic import MagicException
from ocrmypdf import ocr
from sortedcontainers import SortedSet
from tqdm.contrib.concurrent import process_map

from plagdef.model import models

log = logging.getLogger(__name__)
jsonpickle.set_encoder_options('json', indent=4)
lock = Lock()


class DocumentFileRepository:
    @inject
    def __init__(self, dir_path: Path, recursive=False, lang: str = Provide['config.default.lang'],
                 use_ocr: bool = Provide['config.default.ocr', as_(bool)]):
        self.lang = lang
        self.dir_path = dir_path
        self._use_ocr = use_ocr
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
        docs = process_map(self._read_file, files, desc=f"Reading documents in '{self.dir_path}'",
                           unit='doc', total=len(files), max_workers=os.cpu_count())
        return set(filter(None, docs))

    def _read_file(self, file):
        if file.suffix == '.pdf':
            reader = PdfReader(file, self.lang, self._use_ocr)
            text = reader.extract_text()
            return models.Document(file.stem, str(file.resolve()), text)
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


class DocumentPickleRepository:
    def __init__(self, dir_path: Path, common_dir_path: Path = None):
        if not dir_path.is_dir():
            raise NotADirectoryError(f"The given path '{dir_path}' does not point to an existing directory!")
        path_hash = blake2b(str(common_dir_path).encode(), digest_size=16).hexdigest()
        self.file_path = dir_path / f'.{path_hash}.pdef'

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


class PdfReader:
    ERROR_HEURISTIC = '¨[aou]|ﬀ|\(cid:\d+\)|[a-zA-Z]{50}'

    def __init__(self, file, lang, use_ocr):
        self._file = file
        self._lang = lang if lang == 'eng' else 'deu'
        self._use_ocr = use_ocr

    def extract_text(self):
        text = self._extract()
        if self._use_ocr and self._poor_extraction(text):
            log.warning(f"Poor text extraction in '{self._file.name}' detected! Using OCR...")
            with BytesIO() as ocr_file:
                with lock:
                    ocr(self._file, ocr_file, language=self._lang, force_ocr=True, progress_bar=False,
                        max_image_mpixels=512)
                text = self._extract(ocr_file)
        return text

    def _extract(self, file=None) -> str:
        if file is None:
            file = self._file
        with pdfplumber.open(file) as pdf:
            text = ' '.join(filter(None, (page.extract_text() for page in pdf.pages)))
            normalized_text = normalize('NFC', text)
            return re.sub('-\s?\n', '', normalized_text)  # Merge hyphenated words

    def _poor_extraction(self, text: str) -> bool:
        return not len(text.strip()) or bool(re.search(PdfReader.ERROR_HEURISTIC, text))


class UnsupportedFileFormatError(Exception):
    pass
