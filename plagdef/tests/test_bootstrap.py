from unittest.mock import patch

import pytest
from click import UsageError

from plagdef import bootstrap
from plagdef.repositories import ConfigFileRepository, UnsupportedFileFormatError, NoDocumentFilePairFoundError
from plagdef.tests.fakes import DocumentFakeRepository, ConfigFakeRepository, DocumentPairReportFakeRepository


def test_find_matches_without_params_needs_doc_dir_and_lang():
    find_matches = bootstrap.find_matches()
    assert find_matches.func.__name__ == '_needs_doc_dir_and_lang'
    assert isinstance(find_matches.keywords['config_repo'], ConfigFileRepository)


def test_find_matches_with_config_repo_needs_doc_dir_and_lang():
    config_repo = ConfigFakeRepository({})
    find_matches = bootstrap.find_matches(config_repo=config_repo)
    assert find_matches.func.__name__ == '_needs_doc_dir_and_lang'
    assert find_matches.keywords['config_repo'] == config_repo


def test_find_matches_with_doc_repo_needs_no_params():
    doc_repo = DocumentFakeRepository([], 'eng')
    find_matches = bootstrap.find_matches(doc_repo)
    assert find_matches.func.__name__ == 'find_matches'
    assert find_matches.args[0][0] == doc_repo
    assert isinstance(find_matches.args[0][1], ConfigFileRepository)


def test_find_matches_catches_not_a_directory_error():
    find_matches = bootstrap.find_matches()
    with patch('plagdef.bootstrap.DocumentFileRepository', side_effect=NotADirectoryError()):
        with pytest.raises(UsageError):
            find_matches('some/wrong/path', 'eng')


def test_find_matches_catches_unsupported_file_format_error():
    find_matches = bootstrap.find_matches()
    with patch('plagdef.bootstrap.DocumentFileRepository', side_effect=UnsupportedFileFormatError()):
        with pytest.raises(UsageError):
            find_matches('some/path', 'eng')


def test_find_matches_catches_no_document_file_pair_found_error():
    find_matches = bootstrap.find_matches()
    with patch('plagdef.bootstrap.DocumentFileRepository', side_effect=NoDocumentFilePairFoundError()):
        with pytest.raises(UsageError):
            find_matches('some/path', 'eng')


def test_write_xml_reports_without_params_needs_matches_and_xml_dir():
    write_xml_reports = bootstrap.write_xml_reports()
    assert write_xml_reports.__name__ == '_needs_matches_and_xml_dir'


def test_write_xml_reports_with_doc_pair_report_repo_needs_matches():
    doc_pair_report_repo = DocumentPairReportFakeRepository()
    write_xml_reports = bootstrap.write_xml_reports(doc_pair_report_repo)
    assert write_xml_reports.func.__name__ == 'write_xml_reports'
    assert write_xml_reports.keywords['doc_pair_report_repo'] == doc_pair_report_repo


def test_write_xml_reports_catches_not_a_directory_error():
    write_xml_reports = bootstrap.write_xml_reports()
    with patch('plagdef.bootstrap.DocumentPairReportFileRepository', side_effect=NotADirectoryError()):
        with pytest.raises(UsageError):
            write_xml_reports([], 'some/wrong/path')
