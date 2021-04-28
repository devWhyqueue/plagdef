from __future__ import annotations

from pathlib import Path

from plagdef.model.models import Document


class DocumentFakeRepository:
    def __init__(self, documents: [Document], lang: str, dir_path: Path):
        self.lang = lang
        self.dir_path = dir_path
        self._documents = documents

    def list(self) -> set[Document]:
        return set(self._documents)


class ConfigFakeRepository:
    def __init__(self, config: dict):
        self._config = config

    def get(self) -> dict:
        return self._config
