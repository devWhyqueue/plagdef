from pathlib import Path

import pytest

from plagdef.model.reporting import DocumentPairReport
from plagdef.repositories import DocumentPairReportFileRepository
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import config, doc_factory


def test_init_with_nonexistent_out_dir_fails():
    with pytest.raises(NotADirectoryError):
        DocumentPairReportFileRepository(Path('some/wrong/path'))


def test_init_with_file_fails(tmp_path):
    file = tmp_path / 'doc1.txt'
    with file.open('w', encoding='utf-8') as f:
        f.write('Some content.\n')
    with pytest.raises(NotADirectoryError):
        DocumentPairReportFileRepository(file)


def test_add_all_writes_report_files_to_out_path(doc_factory, tmp_path):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document.\n'), \
                 doc_factory.create('doc2', 'This also is a document.\n')
    doc3, doc4 = doc_factory.create('doc3', 'This is another document.\n'), \
                 doc_factory.create('doc4', 'This also is another document.\n')
    repo = DocumentPairReportFileRepository(tmp_path)
    repo.add(DocumentPairReport(doc1, doc2, 'Some content\n', 'fmt'))
    repo.add(DocumentPairReport(doc3, doc4, 'Some other content\n', 'fmt'))
    report_files = sorted(tmp_path.iterdir())
    assert len(report_files) == 2
    assert report_files[0].suffix, report_files[1].suffix == '.fmt'
    assert report_files[0].stem == f'{doc1.name}-{doc2.name}'
    assert report_files[1].stem == f'{doc3.name}-{doc4.name}'
    assert report_files[0].read_text(encoding='utf-8') == 'Some content\n'
    assert report_files[1].read_text(encoding='utf-8') == 'Some other content\n'
