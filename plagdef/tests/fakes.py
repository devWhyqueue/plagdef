from __future__ import annotations

from pathlib import Path

from plagdef.model.models import Document


class DocumentFakeRepository:
    def __init__(self, documents: set[Document], lang: str, base_path: Path):
        self.lang = lang
        self.base_path = base_path
        self._documents = documents

    def list(self) -> set[Document]:
        return self._documents


class FakeDocumentMatcher:
    def __init__(self):
        self.lang = self.preprocessed_docs = self.common_docs = None

    def preprocess(self, lang, docs, common_docs):
        self.lang = lang
        self.preprocessed_docs = docs
        self.common_docs = common_docs


class FakeResponse:
    def __init__(self, headers: dict, content: bytes, text: str):
        self.headers = headers
        self.content = content
        self.text = text

    def raise_for_status(self):
        pass
