from pathlib import Path

import pytest
from fpdf import FPDF

from plagdef.model.preprocessing import Document
from plagdef.repositories import DocumentFileRepository, NoDocumentFilePairFoundError, UnsupportedFileFormatError


def test_init_with_nonexistent_doc_dir_fails():
    with pytest.raises(NotADirectoryError):
        DocumentFileRepository(Path('some/wrong/path'), 'eng')


def test_init_with_file_fails(tmp_path):
    file = tmp_path / 'doc1.txt'
    with file.open('w', encoding='utf-8') as f:
        f.write('Some content.\n')
    with pytest.raises(NotADirectoryError):
        DocumentFileRepository(file, 'eng')


def test_init_with_empty_doc_dir_fails(tmp_path):
    with pytest.raises(NoDocumentFilePairFoundError):
        DocumentFileRepository(tmp_path, 'eng')


def test_init_with_doc_dir_containing_only_one_file_fails(tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('Some content.\n')
    with pytest.raises(NoDocumentFilePairFoundError):
        DocumentFileRepository(Path(tmp_path), 'eng')


def test_init_with_doc_dir_containing_non_utf8_file_fails(tmp_path):
    doc1 = FPDF()
    doc1.add_page()
    doc1.set_font('helvetica', size=12)
    doc1.cell(w=0, txt='Some content')
    doc1.output(f'{tmp_path}/doc1.pdf')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    with pytest.raises(UnsupportedFileFormatError):
        DocumentFileRepository(tmp_path, 'eng')


def test_init_creates_documents(tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('This is a document.\n')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    repo = DocumentFileRepository(tmp_path, 'eng')
    docs = repo.list()
    assert len(docs) == 2
    assert Document('doc1', 'This is a document.\n') in docs
    assert Document('doc2', 'This also is a document.\n') in docs
