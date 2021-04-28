from pathlib import Path

import pytest

from plagdef.repositories import DocumentPairMatchesJsonRepository


def test_init_with_nonexistent_out_dir_fails():
    with pytest.raises(NotADirectoryError):
        DocumentPairMatchesJsonRepository(Path('some/wrong/path'))


def test_init_with_file_fails(tmp_path):
    file = tmp_path / 'doc1.txt'
    with file.open('w', encoding='utf-8') as f:
        f.write('Some content.\n')
    with pytest.raises(NotADirectoryError):
        DocumentPairMatchesJsonRepository(file)


def test_save_doc_pair_matches(tmp_path, matches):
    repo = DocumentPairMatchesJsonRepository(tmp_path)
    [repo.save(m) for m in matches]
    doc_pair_matches = repo.list()
    assert doc_pair_matches == matches


def test_list_if_no_file_exists(tmp_path):
    serializer = DocumentPairMatchesJsonRepository(tmp_path)
    empty = serializer.list()
    assert empty == set()


def test_file_exists_with_corrupt_content(tmp_path):
    file_path = tmp_path / 'doc1-doc2.json'
    with file_path.open('w', encoding='utf-8') as f:
        f.write('Invalid content.')
    repo = DocumentPairMatchesJsonRepository(tmp_path)
    corrupt = repo.list()
    assert corrupt == set()


def test_file_exists_with_wrong_encoding(tmp_path):
    file_path = tmp_path / 'doc1-doc2.json'
    with file_path.open('w', encoding='ASCII') as f:
        f.write('Invalid content.')
    repo = DocumentPairMatchesJsonRepository(tmp_path)
    corrupt = repo.list()
    assert corrupt == set()


def test_file_exists_with_no_content(tmp_path):
    file_path = tmp_path / 'doc1-doc2.json'
    file_path.touch()
    repo = DocumentPairMatchesJsonRepository(tmp_path)
    empty = repo.list()
    assert empty == set()
