from __future__ import annotations

from configparser import ParsingError

from click import UsageError

from plagdef.model.detection import DocumentMatcher
from plagdef.model.models import DocumentPairMatches, Document
from plagdef.model.preprocessing import UnsupportedLanguageError
from plagdef.repositories import UnsupportedFileFormatError, DocumentPickleRepository


def find_matches(doc_repo, config_repo, archive_repo=None, common_doc_repo=None) -> list[DocumentPairMatches]:
    try:
        config = config_repo.get()
        doc_matcher = DocumentMatcher(config)
        common_docs = common_doc_repo.list() if common_doc_repo else None
        archive_docs = None
        if archive_repo:
            archive_docs = _preprocess_docs(doc_matcher, archive_repo, common_docs)
        docs = _preprocess_docs(doc_matcher, doc_repo, common_docs)
        doc_pair_matches = doc_matcher.find_matches(docs, archive_docs)
        return doc_pair_matches
    except (ParsingError, UnsupportedFileFormatError, UnsupportedLanguageError) as e:
        raise UsageError(str(e)) from e


def _preprocess_docs(doc_matcher, doc_repo, common_docs=None) -> set[Document]:
    doc_ser = DocumentPickleRepository(doc_repo.dir_path)
    docs = doc_repo.list()
    prep_docs = {d for d in doc_ser.list() if d in docs}
    unprep_docs = docs.difference(prep_docs)
    doc_matcher.preprocess(doc_repo.lang, unprep_docs, common_docs)
    preprocessed_docs = prep_docs.union(unprep_docs)
    doc_ser.save(preprocessed_docs)
    return preprocessed_docs


def write_json_reports(matches: list[DocumentPairMatches], repo):
    [repo.save(m) for m in matches]
