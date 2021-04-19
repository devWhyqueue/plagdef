from pathlib import Path

import pytest
from fpdf import FPDF

from plagdef.repositories import DocumentFileRepository, NoDocumentFilePairFoundError


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


def test_init_with_doc_dir_containing_only_multiple_files_in_subdirectory(tmp_path):
    subdir = Path(f'{tmp_path}/subdir')
    subdir.mkdir()
    with (subdir / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('Some content.\n')
    with (subdir / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('Some different content.\n')
    DocumentFileRepository(Path(tmp_path), 'eng', recursive=True)


def test_init_with_doc_dir_containing_only_one_file_with_at_least_two_false(tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('Some content.\n')
    DocumentFileRepository(Path(tmp_path), 'eng', at_least_two=False)


def test_list_documents(tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('This is a document.\n')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    Path(f'{tmp_path}/a/dir/that/should/not/be/included').mkdir(parents=True)
    with Path((f'{tmp_path}/a/dir/that/should/not/be/included/doc3.txt')).open('w', encoding='utf-8') as f:
        f.write('The third document.\n')
    repo = DocumentFileRepository(tmp_path, 'eng')
    docs = repo.list()
    assert len(docs) == 2


def test_list_with_file_containing_special_characters(tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('These are typical German umlauts: ä, ö, ü, ß, é and â are rather French.\n')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    repo = DocumentFileRepository(tmp_path, 'eng')
    docs = repo.list()
    assert len(docs) == 2
    assert 'These are typical German umlauts: ä, ö, ü, ß, é and â are rather French.\n' in [doc.text for doc in docs]


@pytest.mark.skipif('sys.platform != "win32"')
def test_list_with_doc_dir_containing_ansi_file_creates_document(tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='ANSI') as f:
        f.write('These are typical German umlauts: ä, ö, ü, ß, é and â are rather French.\n')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    repo = DocumentFileRepository(tmp_path, 'eng')
    docs = repo.list()
    assert len(docs) == 2
    assert 'These are typical German umlauts: ä, ö, ü, ß, é and â are rather French.\n' in [doc.text for doc in docs]


def test_list_with_doc_dir_containing_iso_8559_1_file_creates_documents(tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='ISO-8859-1') as f:
        f.write('These are typical German umlauts: ä, ö, ü, ß, é and â are rather French.\n')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('Hello world, Καλημέρα κόσμε, コンニチハ')
    repo = DocumentFileRepository(tmp_path, 'eng')
    docs = repo.list()
    assert len(docs) == 2
    assert 'These are typical German umlauts: ä, ö, ü, ß, é and â are rather French.\n' in [doc.text for doc in docs]
    assert 'Hello world, Καλημέρα κόσμε, コンニチハ' in [doc.text for doc in docs]


def test_list_recursive_creates_documents(tmp_path):
    with (tmp_path / 'doc1.txt').open('w', encoding='utf-8') as f:
        f.write('This is a document.\n')
    Path(f'{tmp_path}/a/subdir').mkdir(parents=True)
    with Path((f'{tmp_path}/a/subdir/doc2.txt')).open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    Path(f'{tmp_path}/another/sub/even/deeper').mkdir(parents=True)
    with Path((f'{tmp_path}/another/sub/even/deeper/doc3.txt')).open('w', encoding='utf-8') as f:
        f.write('The third document.\n')
    repo = DocumentFileRepository(tmp_path, 'eng', recursive=True)
    docs = repo.list()
    assert len(docs) == 3


def test_list_with_doc_dir_containing_pdf(tmp_path):
    doc1 = FPDF()
    doc1.add_page()
    doc1.set_font('helvetica', size=12)
    doc1.cell(w=0, txt='This is a PDF file containing one sentence.')
    doc1.output(f'{tmp_path}/doc1.pdf')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    repo = DocumentFileRepository(tmp_path, 'eng')
    docs = repo.list()
    assert 'This is a PDF file containing one sentence.' in [doc.text for doc in docs]
    assert 'This also is a document.\n' in [doc.text for doc in docs]


def test_list_with_doc_dir_containing_pdf_with_no_text(tmp_path):
    doc1 = FPDF()
    doc1.add_page()
    doc1.output(f'{tmp_path}/doc1.pdf')
    with (tmp_path / 'doc2.txt').open('w', encoding='utf-8') as f:
        f.write('This also is a document.\n')
    repo = DocumentFileRepository(tmp_path, 'eng')
    docs = repo.list()
    assert len(docs) == 2
    assert 'This also is a document.\n' in [doc.text for doc in docs]
