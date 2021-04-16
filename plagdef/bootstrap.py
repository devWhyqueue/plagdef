from __future__ import annotations

import logging.config
from functools import partial
from pathlib import Path

import pkg_resources
from click import UsageError

from plagdef import services
from plagdef.model.models import DocumentPairMatches
from plagdef.repositories import ConfigFileRepository, DocumentFileRepository, DocumentPairReportFileRepository, \
    NoDocumentFilePairFoundError

LOGGING_CONFIG = pkg_resources.resource_filename(__name__, str(Path('config/logging.ini')))
logging.config.fileConfig(LOGGING_CONFIG, disable_existing_loggers=False)


def find_matches(doc_repo=None, common_doc_repo=None, config_repo=None):
    if not config_repo:
        config_path = pkg_resources.resource_filename(__name__, str(Path('config/alg.ini')))
        config_repo = ConfigFileRepository(Path(config_path))
    if not doc_repo:
        return partial(_needs_doc_dir_and_lang, config_repo=config_repo, common_doc_repo=common_doc_repo)
    else:
        return partial(services.find_matches, (doc_repo, config_repo, common_doc_repo))


def _needs_doc_dir_and_lang(lang: str, doc_dir: str, config_repo, common_doc_repo, recursive=False,
                            common_doc_dir: str = None):
    try:
        doc_repo = DocumentFileRepository(Path(doc_dir), lang, recursive)
        if not common_doc_repo and common_doc_dir:
            common_doc_repo = DocumentFileRepository(Path(common_doc_dir), lang, at_least_two=False)
        return services.find_matches(doc_repo, config_repo, common_doc_repo)
    except (NotADirectoryError, NoDocumentFilePairFoundError) as e:
        raise UsageError(str(e)) from e


def write_xml_reports(doc_pair_report_repo=None):
    if not doc_pair_report_repo:
        return _needs_matches_and_xml_dir
    else:
        return partial(services.write_xml_reports, doc_pair_report_repo=doc_pair_report_repo)


def _needs_matches_and_xml_dir(matches: list[DocumentPairMatches], xml_dir: str):
    try:
        doc_pair_report_repo = DocumentPairReportFileRepository(Path(xml_dir))
        return services.write_xml_reports(matches, doc_pair_report_repo)
    except NotADirectoryError as e:
        raise UsageError(str(e)) from e
