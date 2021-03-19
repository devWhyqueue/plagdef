from configparser import ParsingError

from click import UsageError

from plagdef.model import reporting
from plagdef.model.legacy import algorithm
from plagdef.model.legacy.algorithm import InvalidConfigError
from plagdef.model.preprocessing import UnsupportedLanguageError


def find_matches(doc_repo, config_repo) -> list[algorithm.DocumentPairMatches]:
    try:
        docs = doc_repo.list()
        config = config_repo.get()
        doc_pair_matches = algorithm.find_matches(docs, doc_repo.lang, config)
        return doc_pair_matches
    except (ParsingError, InvalidConfigError, UnsupportedLanguageError) as e:
        raise UsageError(str(e)) from e


def write_xml_reports(matches: list[algorithm.DocumentPairMatches], doc_pair_report_repo):
    doc_pair_reports = reporting.generate_xml_reports(matches)
    for report in doc_pair_reports:
        doc_pair_report_repo.add(report)
