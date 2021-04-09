from __future__ import annotations

from configparser import ParsingError

from click import UsageError

from plagdef.model.detection import DocumentMatcher
from plagdef.model.models import DocumentPairMatches
from plagdef.model.preprocessing import UnsupportedLanguageError
from plagdef.model.reporting import generate_xml_reports


def find_matches(doc_repo, config_repo) -> set[DocumentPairMatches]:
    try:
        docs = doc_repo.list()
        config = config_repo.get()
        doc_matcher = DocumentMatcher(config)
        doc_pair_matches = doc_matcher.find_matches(docs, doc_repo.lang)
        return doc_pair_matches
    except (ParsingError, UnsupportedLanguageError) as e:
        raise UsageError(str(e)) from e


def write_xml_reports(matches: list[DocumentPairMatches], doc_pair_report_repo):
    doc_pair_reports = generate_xml_reports(matches)
    for report in doc_pair_reports:
        doc_pair_report_repo.add(report)
