from configparser import ParsingError
from unittest.mock import patch

import pytest
from click import UsageError

from plagdef.model.detection import DocumentMatcher
from plagdef.model.models import DocumentPairMatches, Match, Fragment, PlagiarismType
from plagdef.model.preprocessing import Document, UnsupportedLanguageError
from plagdef.repositories import UnsupportedFileFormatError
from plagdef.services import find_matches, write_xml_reports
from plagdef.tests.fakes import ConfigFakeRepository, DocumentFakeRepository, DocumentPairReportFakeRepository


def test_find_matches(config):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng')
    config_repo = ConfigFakeRepository(config)
    doc_pair_matches = DocumentPairMatches(PlagiarismType.VERBATIM)
    doc_pair_matches.add(Match(Fragment(0, 18, docs[0]), Fragment(0, 23, docs[1])))
    with patch.object(DocumentMatcher, 'find_matches') as alg_fm:
        alg_fm.return_value = [doc_pair_matches]
        matches = find_matches(doc_repo, config_repo)
    assert matches == [doc_pair_matches]
    alg_fm.assert_called_with(doc_repo.lang, doc_repo.list(), None, None)


def test_find_matches_catches_parsing_error():
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng')
    with patch.object(ConfigFakeRepository, 'get', side_effect=ParsingError('Error!')):
        config_repo = ConfigFakeRepository({})
        with pytest.raises(UsageError):
            find_matches(doc_repo, config_repo)


def test_find_matches_catches_unsupported_language_error(config):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng')
    config_repo = ConfigFakeRepository(config)
    with patch.object(DocumentMatcher, 'find_matches') as alg_fm:
        alg_fm.side_effect = UnsupportedLanguageError()
        with pytest.raises(UsageError):
            find_matches(doc_repo, config_repo)


def test_find_matches_catches_unsupported_file_format_error(config):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng')
    config_repo = ConfigFakeRepository(config)
    with patch.object(DocumentFakeRepository, 'list', side_effect=UnsupportedFileFormatError()):
        with pytest.raises(UsageError):
            find_matches(doc_repo, config_repo)


def test_find_matches_fails_on_unexpected_error(config):
    docs = [Document('doc1', 'path/to/doc1', 'This is a document.\n'),
            Document('doc2', 'path/to/doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs, 'eng')
    config_repo = ConfigFakeRepository(config)
    with patch.object(DocumentMatcher, 'find_matches') as alg_fm:
        alg_fm.side_effect = Exception()
        with pytest.raises(Exception):
            find_matches(doc_repo, config_repo)


def test_write_xml_reports(matches):
    doc_pair_repo = DocumentPairReportFakeRepository()
    write_xml_reports(matches, doc_pair_repo)
    assert len(doc_pair_repo.list()) == 2
