from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from click import UsageError

from plagdef.config import settings
from plagdef.model.detection import DocumentMatcher
from plagdef.model.download import download_all_external_sources
from plagdef.model.models import DocumentPairMatches, Document
from plagdef.model.pipeline.translate import translate, detect_lang, docs_in_other_langs
from plagdef.repositories import UnsupportedFileFormatError, DocumentPickleRepository, DocumentFileRepository, \
    FileRepository

log = logging.getLogger(__name__)


def find_matches(doc_repo, archive_repo=None, common_doc_repo=None, config=settings, download=True) \
    -> list[DocumentPairMatches]:
    try:
        doc_matcher = DocumentMatcher(config)
        archive_docs = None
        if archive_repo:
            archive_docs = _preprocess_docs(doc_matcher, config['ser'], archive_repo, common_doc_repo)
        docs = _preprocess_docs(doc_matcher, config['ser'], doc_repo, common_doc_repo)
        if download and config['download_path']:
            _save_all_external_sources(docs, config['download_path'])
            ext_docs = _preprocess_docs(doc_matcher,
                                        config['ser'],
                                        DocumentFileRepository(Path(config['download_path']), recursive=True),
                                        common_doc_repo, trans=config['transl'])
            archive_docs = archive_docs.union(ext_docs) if archive_docs else ext_docs
        doc_pair_matches = doc_matcher.find_matches(docs, archive_docs)
        return doc_pair_matches
    except UnsupportedFileFormatError as e:
        raise UsageError(str(e)) from e


def _preprocess_docs(doc_matcher, use_serialization, doc_repo, common_doc_repo=None, trans=False) -> set[Document]:
    common_dir_path = common_doc_repo.base_path if common_doc_repo else None
    common_docs = common_doc_repo.list() if common_doc_repo else None
    docs = _translate_docs(doc_repo) if trans else _move_foreign_lang_docs(doc_repo)
    if use_serialization:
        doc_ser = DocumentPickleRepository(doc_repo.base_path, common_dir_path)
        prep_docs = {d for d in doc_ser.list() if d in docs}
        unprep_docs = docs.difference(prep_docs)
        doc_matcher.preprocess(doc_repo.lang, unprep_docs, common_docs)
        preprocessed_docs = prep_docs.union(unprep_docs)
        doc_ser.save(preprocessed_docs)
    else:
        doc_matcher.preprocess(doc_repo.lang, docs, common_docs)
        preprocessed_docs = docs
    return preprocessed_docs


def _save_all_external_sources(docs, download_path):
    external_sources = download_all_external_sources(docs, Path(download_path))
    external_sources_repo = FileRepository(Path(download_path))
    external_sources_repo.save_all(external_sources)


def _translate_docs(doc_repo: DocumentFileRepository) -> set[Document]:
    docs = doc_repo.list()
    detect_lang(docs)
    translated_docs = translate(docs_in_other_langs(docs, doc_repo.lang), doc_repo.lang)
    if len(translated_docs):
        for doc in translated_docs:
            new_path = str(Path(doc.path).with_name(f"{doc.name}_trans.txt"))
            doc_repo.remove_all({doc})
            doc.path = new_path
        doc_repo.save_all(translated_docs)
    return {doc for doc in docs if doc.lang == doc_repo.lang}


def _move_foreign_lang_docs(doc_repo: DocumentFileRepository) -> set[Document]:
    docs = doc_repo.list()
    detect_lang(docs)
    foreign_docs = docs_in_other_langs(docs, doc_repo.lang)
    foreign_dir = os.path.join(doc_repo.base_path, 'foreign_lang')
    os.makedirs(foreign_dir, exist_ok=True)
    for doc in foreign_docs:
        file_name = os.path.basename(doc.path)
        new_file_path = os.path.join(foreign_dir, file_name)
        shutil.move(doc.path, new_file_path)
        doc.path = new_file_path
    return docs


def write_json_reports(matches: list[DocumentPairMatches], repo):
    [repo.save(m) for m in matches]
