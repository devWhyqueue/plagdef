from configparser import ParsingError
from pathlib import Path

import pytest

from plagdef.repositories import ConfigFileRepository, UnsupportedFileFormatError


def test_init_with_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        ConfigFileRepository(Path('some/wrong/path'))


def test_init_with_wrong_file_format(tmp_path):
    file = tmp_path / 'config.txt'
    with file.open('w', encoding='utf-8') as f:
        f.write('param1=5\n')
    with pytest.raises(UnsupportedFileFormatError):
        ConfigFileRepository(file)


def test_init_with_directory_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        ConfigFileRepository(tmp_path)


def test_get_returns_all_properties(tmp_path):
    file = tmp_path / 'config.ini'
    with file.open('w', encoding='utf-8') as f:
        f.write('[section1]\nparam1=5\n\n[section2]\nparam2=3\n')
    repo = ConfigFileRepository(file)
    config = repo.get()
    assert config.get('param1') == 5
    assert config.get('param2') == 3


def test_update(tmp_path):
    file = tmp_path / 'config.ini'
    with file.open('w', encoding='utf-8') as f:
        f.write('[section1]\nparam1=5\n\n[section2]\nparam2=3\n')
    repo = ConfigFileRepository(file)
    repo.update({'param1': 10, 'param2': 6})
    config = repo.get()
    file_content = file.read_text(encoding='utf-8')
    assert config.get('param1') == 10 and config.get('param2') == 6
    assert 'param1=5' in file_content and 'param2=3' in file_content


def test_get_with_invalid_config_fails(tmp_path):
    file = tmp_path / 'config.ini'
    with file.open('w', encoding='utf-8') as f:
        f.write('param1=5\nparam2=3\n')
    repo = ConfigFileRepository(file)
    with pytest.raises(ParsingError):
        repo.get()
