#!/usr/bin/env python

from unittest.mock import MagicMock, ANY

from click import UsageError
from click.testing import CliRunner

from plagdef import app
from plagdef.app import cli


def test_cli_if_no_matches_found(tmp_path):
    app.find_matches = MagicMock(return_value=[])
    runner = CliRunner()
    result = runner.invoke(cli, ['-l', 'eng', str(tmp_path)])
    app.find_matches.assert_called_with(ANY, ANY, recursive=False)
    assert result.exit_code == 0
    assert result.output == 'Found no suspicious document pair.\n\n'


def test_cli_if_one_match_found(matches, tmp_path):
    app.find_matches = MagicMock(return_value=[matches[0]])
    runner = CliRunner()
    result = runner.invoke(cli, ['-l', 'eng', str(tmp_path)])
    assert result.exit_code == 0
    assert result.output.startswith('Found 1 suspicious document pair.\n')


def test_cli_if_multiple_matches_found(matches, tmp_path):
    app.find_matches = MagicMock(return_value=matches)
    runner = CliRunner()
    result = runner.invoke(cli, ['-l', 'eng', str(tmp_path)])
    assert result.exit_code == 0
    assert result.output.startswith('Found 2 suspicious document pairs.\n')


def test_cli_with_recursive_option(tmp_path):
    app.find_matches = MagicMock()
    runner = CliRunner()
    result = runner.invoke(cli, ['-l', 'eng', '-R', str(tmp_path)])
    app.find_matches.assert_called_with(ANY, ANY, recursive=True)
    assert result.exit_code == 0


def test_text_report_with_matches_is_printed(matches, tmp_path):
    app.find_matches = MagicMock(return_value=matches)
    runner = CliRunner()
    result = runner.invoke(cli, ['-l', 'eng', str(tmp_path)])
    assert result.exit_code == 0
    assert 'Match(Fragment(0, 5), Fragment(0, 5))' in result.output
    assert 'Match(Fragment(5, 10), Fragment(5, 10))' in result.output
    assert 'Match(Fragment(2, 6), Fragment(2, 8))' in result.output \
           or 'Match(Fragment(2, 8), Fragment(2, 6))' in result.output


def test_confirmation_after_xml_reports_are_generated(matches, tmp_path):
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'out').mkdir()
    app.find_matches = MagicMock(return_value=matches)
    runner = CliRunner()
    result = runner.invoke(cli, ['-l', 'eng', str((tmp_path / 'docs')), '-x', str((tmp_path / 'out'))])
    assert result.exit_code == 0
    assert f'Successfully wrote XML reports to {(tmp_path / "out")}.' in result.output


def test_usage_error_caught(tmp_path):
    app.find_matches = MagicMock(side_effect=UsageError('An error'))
    runner = CliRunner()
    result = runner.invoke(cli, ['-l', 'eng', str(tmp_path)])
    assert result.exit_code == 2
