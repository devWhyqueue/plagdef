from pathlib import Path

import pytest
from fpdf import FPDF

from plagdef.repositories import DocumentFileRepository, NoDocumentFilePairFoundError, UnsupportedFileFormatError
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import config, doc_factory


def test_init_with_nonexistent_doc_dir_fails(doc_factory):
    with pytest.raises(NotADirectoryError):
        DocumentFileRepository(Path('some/wrong/path'), doc_factory)


def test_init_with_file_fails(tmp_path, doc_factory):
    file = tmp_path / 'doc1.txt'
    with file.open('w', encoding='utf-8') as f:
        f.write('Some content.\n')
    with pytest.raises(NotADirectoryError):
        DocumentFileRepository(file, doc_factory)


def test_init_with_empty_doc_dir_fails(tmp_path, doc_factory):
    with pytest.raises(NoDocumentFilePairFoundError):
        DocumentFileRepository(tmp_path, doc_factory)


def test_init_with_doc_dir_containing_only_one_file_fails(tmp_path, doc_factory):
    with (tmp_path / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('Some content.\n')
    with pytest.raises(NoDocumentFilePairFoundError):
        DocumentFileRepository(Path(tmp_path), doc_factory)


def test_init_with_doc_dir_containing_non_utf8_file_fails(tmp_path, doc_factory):
    doc1 = FPDF()
    doc1.add_page()
    doc1.set_font('helvetica', size=12)
    doc1.cell(w=0, txt='Some content')
    doc1.output(f'{tmp_path}/doc1.pdf')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    with pytest.raises(UnsupportedFileFormatError):
        DocumentFileRepository(tmp_path, doc_factory)


def test_init_creates_documents(doc_factory, tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('This is a document.\n')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    repo = DocumentFileRepository(tmp_path, doc_factory)
    docs = repo.list()
    assert len(docs) == 2
    assert doc_factory.create('doc1', 'This is a document.\n') in docs
    assert doc_factory.create('doc2', 'This also is a document.\n') in docs
