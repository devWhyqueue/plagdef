import pytest
from pytest import fixture

from plagdef.algorithm import find_matches, Document, InvalidConfigError, Match, Section, DocumentPairMatches, \
    DifferentDocumentPairError


@fixture
def config():
    return {
        'th1': 0.3, 'th2': 0.33, 'th3': 0.34,
        'src_gap': 4, 'src_gap_least': 0, 'susp_gap': 4, 'susp_gap_least': 0,
        'verbatim_minlen': 256, 'src_size': 1, 'susp_size': 1, 'min_sentlen': 3, 'min_plaglen': 15,
        'rssent': 0, 'tf_idf_p': 0, 'rem_sw': 0,
        'verbatim': 1, 'summary': 1, 'src_gap_summary': 24, 'susp_gap_summary': 24
    }


def test_doc_pair_doc1():
    doc1, doc2 = Document('doc1', 'This is a document.\n'), Document('doc2', 'This also is a document.\n')
    doc_pair_matches = DocumentPairMatches()
    doc_pair_matches.add(Match(Section(doc1, 0, 5), Section(doc2, 0, 5)))
    assert doc_pair_matches.doc1 == doc1


def test_doc_pair_doc2():
    doc1, doc2 = Document('doc1', 'This is a document.\n'), Document('doc2', 'This also is a document.\n')
    doc_pair_matches = DocumentPairMatches()
    doc_pair_matches.add(Match(Section(doc1, 0, 5), Section(doc2, 0, 5)))
    assert doc_pair_matches.doc2 == doc2


def test_doc_pair_doc1_without_matches_returns_nothing():
    doc_pair_matches = DocumentPairMatches()
    assert not doc_pair_matches.doc1


def test_doc_pair_doc2_without_matches_returns_nothing():
    doc_pair_matches = DocumentPairMatches()
    assert not doc_pair_matches.doc2


def test_doc_pair_matches_add():
    doc1, doc2 = Document('doc1', 'This is a document.\n'), Document('doc2', 'This also is a document.\n')
    match1, match2 = Match(Section(doc1, 0, 5), Section(doc2, 0, 5)), Match(Section(doc1, 5, 10), Section(doc2, 5, 10))
    doc_pair_matches = DocumentPairMatches()
    doc_pair_matches.add(match1)
    doc_pair_matches.add(match2)
    assert len(doc_pair_matches.list()) == 2
    assert match1, match2 in doc_pair_matches.list()


def test_doc_pair_matches_add_match_from_other_pair_fails():
    doc1, doc2 = Document('doc1', 'This is a document.\n'), Document('doc2', 'This also is a document.\n')
    doc3, doc4 = Document('doc3', 'This is another document.\n'), Document('doc4', 'This also is another document.\n')
    match1, match2 = Match(Section(doc1, 0, 5), Section(doc2, 0, 5)), Match(Section(doc3, 5, 10), Section(doc4, 5, 10))
    doc_pair_matches = DocumentPairMatches()
    doc_pair_matches.add(match1)
    with pytest.raises(DifferentDocumentPairError):
        doc_pair_matches.add(match2)
    assert len(doc_pair_matches.list()) == 1


def test_find_matches_without_documents_returns_empty_list(config):
    matches = find_matches([], config)
    assert len(matches) == 0


def test_find_matches_without_config_fails():
    docs = [Document('doc1', 'This is a document.\n'), Document('doc2', 'This is a document.\n')]
    with pytest.raises(InvalidConfigError):
        find_matches(docs, {})


def test_find_matches_returns_a_match(config):
    docs = [Document('doc1', 'This is an awesome document.\n'), Document('doc2', 'This is an awesome document.\n')]
    matches = find_matches(docs, config)
    assert len(matches) == 1
