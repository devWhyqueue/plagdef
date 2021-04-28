from configparser import ParsingError
from unittest.mock import patch

import pytest
from click import UsageError

from plagdef.model.detection import DocumentMatcher
from plagdef.model.models import DocumentPairMatches, Match, Fragment, MatchType
from plagdef.model.preprocessing import Document, UnsupportedLanguageError
from plagdef.repositories import UnsupportedFileFormatError, DocumentPairMatchesJsonRepository
from plagdef.services import find_matches, write_json_reports
from plagdef.tests.fakes import ConfigFakeRepository, DocumentFakeRepository


def test_find_matches(config, tmp_path):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng', tmp_path)
    config_repo = ConfigFakeRepository(config)
    doc_pair_matches = DocumentPairMatches(docs[0], docs[1])
    doc_pair_matches.add(Match(MatchType.VERBATIM, Fragment(0, 18, docs[0]), Fragment(0, 23, docs[1])))
    with patch.object(DocumentMatcher, 'find_matches') as alg_fm:
        alg_fm.return_value = [doc_pair_matches]
        matches = find_matches(doc_repo, config_repo)
    assert matches == [doc_pair_matches]
    alg_fm.assert_called_with(doc_repo.list(), None)


def test_find_matches_catches_parsing_error(tmp_path):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng', tmp_path)
    with patch.object(ConfigFakeRepository, 'get', side_effect=ParsingError('Error!')):
        config_repo = ConfigFakeRepository({})
        with pytest.raises(UsageError):
            find_matches(doc_repo, config_repo)


def test_find_matches_catches_unsupported_language_error(config, tmp_path):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng', tmp_path)
    config_repo = ConfigFakeRepository(config)
    with patch.object(DocumentMatcher, 'find_matches') as alg_fm:
        alg_fm.side_effect = UnsupportedLanguageError()
        with pytest.raises(UsageError):
            find_matches(doc_repo, config_repo)


def test_find_matches_catches_unsupported_file_format_error(config, tmp_path):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng', tmp_path)
    config_repo = ConfigFakeRepository(config)
    with patch.object(DocumentFakeRepository, 'list', side_effect=UnsupportedFileFormatError()):
        with pytest.raises(UsageError):
            find_matches(doc_repo, config_repo)


def test_find_matches_fails_on_unexpected_error(config, tmp_path):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng', tmp_path)
    config_repo = ConfigFakeRepository(config)
    with patch.object(DocumentMatcher, 'find_matches') as alg_fm:
        alg_fm.side_effect = Exception()
        with pytest.raises(Exception):
            find_matches(doc_repo, config_repo)


def test_write_xml_reports(matches, tmp_path):
    doc_pair_repo = DocumentPairMatchesJsonRepository(tmp_path)
    write_json_reports(matches, doc_pair_repo)
    assert len(doc_pair_repo.list()) == 2
