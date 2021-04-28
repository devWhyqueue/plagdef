from collections import Counter
from pickle import dump, load

import pytest

from plagdef.model.models import Document, Fragment, Sentence
from plagdef.repositories import DocumentPickleRepository


def test_serialize_docs(tmp_path):
    docs = {Document('doc1', 'path/to/doc1', 'Some text.'), Document('doc2', 'path/to/doc2', 'Different text.')}
    serializer = DocumentPickleRepository(tmp_path)
    serializer.save(docs)
    deserialized_docs = serializer.list()
    assert deserialized_docs == docs


def test_serialize_docs_if_file_exists(tmp_path):
    docs = {Document('doc1', 'path/to/doc1', 'Some text.'), Document('doc2', 'path/to/doc2', 'Different text.')}
    serializer = DocumentPickleRepository(tmp_path)
    serializer.save(docs)
    doc3 = Document('doc3', 'path/to/doc3', 'Another document.')
    serializer.save({doc3})
    deserialized_docs = serializer.list()
    assert deserialized_docs == {*docs, doc3}


def test_deserialize_if_no_file_exists(tmp_path):
    serializer = DocumentPickleRepository(tmp_path)
    deserialized_docs = serializer.list()
    assert deserialized_docs == set()


def test_init_with_file_fails(tmp_path):
    file_path = tmp_path / 'test.file'
    with file_path.open('w', encoding='utf-8') as f:
        f.write('Content.')
    with pytest.raises(NotADirectoryError):
        DocumentPickleRepository(file_path)


def test_file_exists_with_corrupt_content(tmp_path):
    file_path = tmp_path / DocumentPickleRepository.FILE_NAME
    with file_path.open('w', encoding='utf-8') as f:
        f.write('Invalid content.')
    ser = DocumentPickleRepository(tmp_path)
    docs = ser.list()
    assert docs == set()


def test_file_exists_with_no_content(tmp_path):
    file_path = tmp_path / DocumentPickleRepository.FILE_NAME
    file_path.touch()
    ser = DocumentPickleRepository(tmp_path)
    docs = ser.list()
    assert docs == set()


def test_pickle_fragment(tmp_path):
    frag = Fragment(0, 1, Document('doc', 'path/to/doc', 'Content.'))
    with (tmp_path / 'pickle.dat').open('wb') as file:
        dump(frag, file)
    with (tmp_path / 'pickle.dat').open('rb') as file:
        unpickled_frag = load(file)
    assert frag == unpickled_frag


def test_pickle_sentence(tmp_path):
    sent = Sentence(0, 1, Counter(), Document('doc', 'path/to/doc', 'Content.'))
    with (tmp_path / 'pickle.dat').open('wb') as file:
        dump(sent, file)
    with (tmp_path / 'pickle.dat').open('rb') as file:
        unpickled_sent = load(file)
    assert sent == unpickled_sent


def test_pickle_document_with_sentence(tmp_path):
    doc = Document('doc', 'path/to/doc', 'Content.')
    sent = Sentence(0, 1, Counter(), doc)
    doc.add_sent(sent)
    with (tmp_path / 'pickle.dat').open('wb') as file:
        dump(doc, file)
    with (tmp_path / 'pickle.dat').open('rb') as file:
        unpickled_doc = load(file)
    assert doc == unpickled_doc
