#!/usr/bin/env python

from unittest.mock import patch

from click.testing import CliRunner

from plagdef.cli import main
from plagdef.model.legacy.algorithm import InvalidConfigError
from plagdef.model.preprocessing import UnsupportedLanguageError
from plagdef.repositories import UnsupportedFileFormatError, NoDocumentFilePairFoundError
from plagdef.tests.fakes import ConfigFakeRepository, DocumentFakeRepository, DocumentPairReportFakeRepository
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import matches, doc_factory, config


def test_output_if_no_matches_found(tmp_path, config):
    with patch('plagdef.cli.DocumentFileRepository', return_value=DocumentFakeRepository([])), \
        patch('plagdef.cli.ConfigFileRepository', return_value=ConfigFakeRepository(config)), \
        patch('plagdef.cli.find_matches', return_value=[]):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', '-l', 'eng', str(tmp_path)])
    assert result.exit_code == 0
    assert result.output == 'Found no suspicious document pair.\n\n'


def test_output_if_one_match_found(matches, tmp_path, config):
    with patch('plagdef.cli.DocumentFileRepository', return_value=DocumentFakeRepository([])), \
        patch('plagdef.cli.ConfigFileRepository', return_value=ConfigFakeRepository(config)), \
        patch('plagdef.cli.find_matches', return_value=[matches[0]]):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
    assert result.exit_code == 0
    assert result.output.startswith('Found 1 suspicious document pair.\n')


def test_output_if_multiple_matches_found(matches, tmp_path, config):
    with patch('plagdef.cli.DocumentFileRepository', return_value=DocumentFakeRepository([])), \
        patch('plagdef.cli.ConfigFileRepository', return_value=ConfigFakeRepository(config)), \
        patch('plagdef.cli.find_matches', return_value=matches):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
    assert result.exit_code == 0
    assert result.output.startswith('Found 2 suspicious document pairs.\n')


def test_text_report_with_matches_is_printed(matches, tmp_path, config):
    with patch('plagdef.cli.DocumentFileRepository', return_value=DocumentFakeRepository([])), \
        patch('plagdef.cli.ConfigFileRepository', return_value=ConfigFakeRepository(config)), \
        patch('plagdef.cli.find_matches', return_value=matches):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
    assert result.exit_code == 0
    assert 'Pair(doc1, doc2):\n' \
           '  Match(Section(0, 5), Section(0, 5))\n' \
           '  Match(Section(5, 10), Section(5, 10))\n' \
           'Pair(doc3, doc4):\n' \
           '  Match(Section(2, 6), Section(2, 8))\n' in result.output


def test_confirmation_after_xml_reports_are_generated(matches, tmp_path, config):
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'out').mkdir()
    with patch('plagdef.cli.DocumentFileRepository', return_value=DocumentFakeRepository([])), \
        patch('plagdef.cli.ConfigFileRepository', return_value=ConfigFakeRepository(config)), \
        patch('plagdef.cli.DocumentPairReportFileRepository', return_value=DocumentPairReportFakeRepository()), \
        patch('plagdef.cli.find_matches', return_value=matches):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str((tmp_path / 'docs')), '-x', str((tmp_path / 'out'))])
    assert result.exit_code == 0
    assert f'Successfully wrote XML reports to {(tmp_path / "out")}.' in result.output


def test_not_a_directory_error_caught(tmp_path):
    with patch('plagdef.cli.DocumentFileRepository', side_effect=NotADirectoryError()):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
        assert result.exit_code == 2


def test_no_document_file_pair_found_error_caught(tmp_path):
    with patch('plagdef.cli.DocumentFileRepository', side_effect=NoDocumentFilePairFoundError()):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
        print(result.output)
        assert result.exit_code == 2


def test_unsupported_file_format_error_caught(tmp_path):
    with patch('plagdef.cli.DocumentFileRepository', side_effect=UnsupportedFileFormatError()):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
        assert result.exit_code == 2


def test_file_not_found_error_caught(tmp_path):
    with patch('plagdef.cli.DocumentFileRepository', return_value=DocumentFakeRepository([])), \
        patch('plagdef.cli.ConfigFileRepository', side_effect=FileNotFoundError()):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
    assert result.exit_code == 2


def test_invalid_config_error_caught(tmp_path, config):
    with patch('plagdef.cli.DocumentFileRepository', return_value=DocumentFakeRepository([])), \
        patch('plagdef.cli.ConfigFileRepository', return_value=ConfigFakeRepository(config)), \
        patch('plagdef.cli.find_matches', side_effect=InvalidConfigError()):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
        assert result.exit_code == 2


def test_unsupported_language_error_caught(tmp_path):
    with patch('plagdef.cli.DocumentFileRepository', side_effect=UnsupportedLanguageError()):
        runner = CliRunner()
        result = runner.invoke(main, ['-l', 'eng', str(tmp_path)])
        assert result.exit_code == 2
