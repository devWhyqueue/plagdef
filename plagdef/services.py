from __future__ import annotations

from configparser import ParsingError

from click import UsageError

from plagdef.model.detection import DocumentMatcher
from plagdef.model.models import DocumentPairMatches, PlagiarismType, Document
from plagdef.model.preprocessing import UnsupportedLanguageError
from plagdef.model.reporting import generate_xml_reports
from plagdef.repositories import UnsupportedFileFormatError, DocumentSerializer


def find_matches(doc_repo, config_repo, archive_repo=None, common_doc_repo=None) \
    -> dict[PlagiarismType, list[DocumentPairMatches]]:
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
    doc_ser = DocumentSerializer(doc_repo.dir_path)
    prep_docs = doc_ser.deserialize()
    unprep_docs = doc_repo.list().difference(prep_docs)
    doc_matcher.preprocess(doc_repo.lang, unprep_docs, common_docs)
    docs = prep_docs.union(unprep_docs)
    doc_ser.serialize(docs)
    return docs


def write_xml_reports(matches: dict[PlagiarismType, list[DocumentPairMatches]], doc_pair_report_repo):
    doc_pair_reports = generate_xml_reports(matches)
    for report in doc_pair_reports:
        doc_pair_report_repo.add(report)
