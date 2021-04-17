from __future__ import annotations

from configparser import ParsingError

from click import UsageError

from plagdef.model.detection import DocumentMatcher
from plagdef.model.models import DocumentPairMatches
from plagdef.model.preprocessing import UnsupportedLanguageError
from plagdef.model.reporting import generate_xml_reports
from plagdef.repositories import UnsupportedFileFormatError


def find_matches(doc_repo, config_repo, common_doc_repo=None) -> list[DocumentPairMatches]:
    try:
        docs = list(doc_repo.list())
        common_docs = list(common_doc_repo.list()) if common_doc_repo else None
        config = config_repo.get()
        doc_matcher = DocumentMatcher(config)
        doc_pair_matches = doc_matcher.find_matches(doc_repo.lang, docs, common_docs)
        return doc_pair_matches
    except (ParsingError, UnsupportedFileFormatError, UnsupportedLanguageError) as e:
        raise UsageError(str(e)) from e


def write_xml_reports(matches: list[DocumentPairMatches], doc_pair_report_repo):
    doc_pair_reports = generate_xml_reports(matches)
    for report in doc_pair_reports:
        doc_pair_report_repo.add(report)
