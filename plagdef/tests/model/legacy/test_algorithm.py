import pytest

from plagdef.model.legacy.algorithm import find_matches, InvalidConfigError, Match, Section, DocumentPairMatches, \
    DifferentDocumentPairError
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import doc_factory, config


def test_doc_pair_doc1(doc_factory):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document.\n'), \
                 doc_factory.create('doc2', 'This also is a document.\n')

    doc_pair_matches = DocumentPairMatches()
    doc_pair_matches.add(Match(Section(doc1, 0, 5), Section(doc2, 0, 5)))
    assert doc_pair_matches.doc1 == doc1


def test_doc_pair_doc2(doc_factory):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document.\n'), \
                 doc_factory.create('doc2', 'This also is a document.\n')
    doc_pair_matches = DocumentPairMatches()
    doc_pair_matches.add(Match(Section(doc1, 0, 5), Section(doc2, 0, 5)))
    assert doc_pair_matches.doc2 == doc2


def test_doc_pair_doc1_without_matches_returns_nothing():
    doc_pair_matches = DocumentPairMatches()
    assert not doc_pair_matches.doc1


def test_doc_pair_doc2_without_matches_returns_nothing():
    doc_pair_matches = DocumentPairMatches()
    assert not doc_pair_matches.doc2


def test_doc_pair_matches_add(doc_factory):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document.\n'), \
                 doc_factory.create('doc2', 'This also is a document.\n')
    match1, match2 = Match(Section(doc1, 0, 5), Section(doc2, 0, 5)), Match(Section(doc1, 5, 10), Section(doc2, 5, 10))
    doc_pair_matches = DocumentPairMatches()
    doc_pair_matches.add(match1)
    doc_pair_matches.add(match2)
    assert len(doc_pair_matches.list()) == 2
    assert match1, match2 in doc_pair_matches.list()


def test_doc_pair_matches_add_match_from_other_pair_fails(doc_factory):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document.\n'), \
                 doc_factory.create('doc2', 'This also is a document.\n')
    doc3, doc4 = doc_factory.create('doc3', 'This is another document.\n'), \
                 doc_factory.create('doc4', 'This also is another document.\n')
    match1, match2 = Match(Section(doc1, 0, 5), Section(doc2, 0, 5)), Match(Section(doc3, 5, 10), Section(doc4, 5, 10))
    doc_pair_matches = DocumentPairMatches()
    doc_pair_matches.add(match1)
    with pytest.raises(DifferentDocumentPairError):
        doc_pair_matches.add(match2)
    assert len(doc_pair_matches.list()) == 1


def test_find_matches_without_documents_returns_empty_list(config):
    matches = find_matches([], config)
    assert len(matches) == 0


def test_find_matches_without_config_fails(doc_factory):
    docs = [doc_factory.create('doc1', 'This is a document.\n'),
            doc_factory.create('doc2', 'This also is a document.\n')]
    with pytest.raises(InvalidConfigError):
        find_matches(docs, {})


def test_find_matches_returns_a_match(doc_factory, config):
    docs = [doc_factory.create('doc1', 'This is an awesome document. And some text in it.\n'),
            doc_factory.create('doc2', 'It\'s a great one. This is an awesome document.\n')]
    matches = find_matches(docs, config)
    assert len(matches) == 1
