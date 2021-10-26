from unittest.mock import patch

from plagdef.model.detection import DocumentMatcher
from plagdef.model.matching import Pipeline
from plagdef.model.models import Document


@patch('plagdef.model.detection.parallelize')
def test_find_matches(method, config):
    docs = [Document(f'doc{i}', f'/some/path/to/doc{i}', "Some text.") for i in range(3)]
    doc_matcher = DocumentMatcher(config)
    doc_matcher.find_matches(docs)
    assert set(method.call_args.args[1]) == {(Document('doc0', '/some/path/to/doc0', 'Some text.'),
                                              Document('doc1', '/some/path/to/doc1', 'Some text.')),
                                             (Document('doc0', '/some/path/to/doc0', 'Some text.'),
                                              Document('doc2', '/some/path/to/doc2', 'Some text.')),
                                             (Document('doc1', '/some/path/to/doc1', 'Some text.'),
                                              Document('doc2', '/some/path/to/doc2', 'Some text.'))
                                             }


@patch('plagdef.model.detection.parallelize')
def test_find_matches_with_archive_docs(method, config):
    docs = {Document(f'doc{i}', f'/some/path/to/doc{i}', f"Some text.{i}") for i in range(3)}
    archive_docs = {Document(f'doc{i}', f'/some/path/to/doc{i}', f"Some text.{i}") for i in range(3, 5)}
    doc_matcher = DocumentMatcher(config)
    doc_matcher.find_matches(docs, archive_docs)
    assert {frozenset(tpl) for tpl in method.call_args.args[1]} == \
           {frozenset(docset) for docset in ({Document('doc0', '/some/path/to/doc0', 'Some text.0'),
                                              Document('doc1', '/some/path/to/doc1', 'Some text.1')},
                                             {Document('doc0', '/some/path/to/doc0', 'Some text.0'),
                                              Document('doc2', '/some/path/to/doc2', 'Some text.2')},
                                             {Document('doc1', '/some/path/to/doc1', 'Some text.1'),
                                              Document('doc2', '/some/path/to/doc2', 'Some text.2')},

                                             {Document('doc0', '/some/path/to/doc0', 'Some text.0'),
                                              Document('doc3', '/some/path/to/doc3', 'Some text.3')},
                                             {Document('doc0', '/some/path/to/doc0', 'Some text.0'),
                                              Document('doc4', '/some/path/to/doc4', 'Some text.4')},
                                             {Document('doc1', '/some/path/to/doc1', 'Some text.1'),
                                              Document('doc3', '/some/path/to/doc3', 'Some text.3')},
                                             {Document('doc1', '/some/path/to/doc1', 'Some text.1'),
                                              Document('doc4', '/some/path/to/doc4', 'Some text.4')},
                                             {Document('doc2', '/some/path/to/doc2', 'Some text.2'),
                                              Document('doc3', '/some/path/to/doc3', 'Some text.3')},
                                             {Document('doc2', '/some/path/to/doc2', 'Some text.2'),
                                              Document('doc4', '/some/path/to/doc4', 'Some text.4')},
                                             )}


@patch('plagdef.model.detection.parallelize')
def test_find_matches_with_identical_doc_in_both_archive_and_docs(method, config):
    docs = {Document(f'doc1', f'/some/path/to/doc1', "Identical text.")}
    archive_docs = {Document(f'doc2', f'/some/path/to/doc2', "Identical text.")}
    doc_matcher = DocumentMatcher(config)
    doc_matcher.find_matches(docs, archive_docs)
    assert not len(method.call_args.args[1])


@patch.object(Pipeline, 'find_matches', return_value=[])
def test__find_matches(config):
    doc_matcher = DocumentMatcher(config)
    matches = doc_matcher._find_matches([(Document('doc0', '/some/path/to/doc0', 'Some text.'),
                                          Document('doc1', '/some/path/to/doc1', 'Some text.'))])
    assert matches == []
