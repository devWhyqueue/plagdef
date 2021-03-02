from os import listdir
from os.path import join, isfile
from pathlib import Path

import model


class DocumentFileRepository:
    def __init__(self, dir_path: Path):
        doc_files = [Path(join(dir_path, f)) for f in listdir(dir_path) if isfile(join(dir_path, f))]
        self._documents = [model.Document(f.stem, f.read_text(encoding='utf-8')) for f in doc_files]

    def get(self, name: str):
        return next(d for d in self._documents if d.name == name)

    def list(self):
        return self._documents
