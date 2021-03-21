from __future__ import annotations

import pathlib
from functools import partial

import pkg_resources
from click import UsageError

from plagdef import services
from plagdef.model.legacy.algorithm import DocumentPairMatches
from plagdef.repositories import ConfigFileRepository, DocumentFileRepository, DocumentPairReportFileRepository, \
    UnsupportedFileFormatError, NoDocumentFilePairFoundError

CONFIG_PATH = pathlib.Path('config/alg.ini')


def find_matches(doc_repo=None, config_repo=None):
    if not config_repo:
        config_path = pkg_resources.resource_filename(__name__, str(CONFIG_PATH))
        config_repo = ConfigFileRepository(pathlib.Path(config_path))
    if not doc_repo:
        return partial(_needs_doc_dir_and_lang, config_repo=config_repo)
    else:
        return partial(services.find_matches, (doc_repo, config_repo))


def _needs_doc_dir_and_lang(doc_dir: str, lang: str, config_repo, recursive=False):
    try:
        doc_repo = DocumentFileRepository(pathlib.Path(doc_dir), lang, recursive)
        return services.find_matches(doc_repo, config_repo)
    except (NotADirectoryError, UnsupportedFileFormatError, NoDocumentFilePairFoundError) as e:
        raise UsageError(str(e)) from e


def write_xml_reports(doc_pair_report_repo=None):
    if not doc_pair_report_repo:
        return _needs_matches_and_xml_dir
    else:
        return partial(services.write_xml_reports, doc_pair_report_repo=doc_pair_report_repo)


def _needs_matches_and_xml_dir(matches: list[DocumentPairMatches], xml_dir: str):
    try:
        doc_pair_report_repo = DocumentPairReportFileRepository(pathlib.Path(xml_dir))
        return services.write_xml_reports(matches, doc_pair_report_repo)
    except NotADirectoryError as e:
        raise UsageError(str(e)) from e
