import pytest
from pytest import fixture

from plagdef.algorithm import find_matches, Document, InvalidConfigError


@fixture
def config():
    return {
        'th1': 0.3, 'th2': 0.33, 'th3': 0.34,
        'src_gap': 4, 'src_gap_least': 0, 'susp_gap': 4, 'susp_gap_least': 0,
        'verbatim_minlen': 256, 'src_size': 1, 'susp_size': 1, 'min_sentlen': 3, 'min_plaglen': 15,
        'rssent': 0, 'tf_idf_p': 0, 'rem_sw': 0,
        'verbatim': 1, 'summary': 1, 'src_gap_summary': 24, 'susp_gap_summary': 24
    }


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
