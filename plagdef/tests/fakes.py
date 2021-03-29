from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from plagdef.model.legacy.algorithm import Document
from plagdef.model.reporting import DocumentPairReport


class DocumentPairReportFakeRepository:
    def __init__(self):
        self._doc_pair_reports = []

    def add(self, report: DocumentPairReport):
        self._doc_pair_reports.append(report)

    def list(self) -> [DocumentPairReport]:
        return self._doc_pair_reports


class DocumentFakeRepository:
    def __init__(self, documents: [Document], lang: str):
        self.lang = lang
        self._documents = documents

    def list(self) -> [Document]:
        return self._documents


class ConfigFakeRepository:
    def __init__(self, config: dict):
        self._config = config

    def get(self) -> dict:
        return self._config


@dataclass
class FakeSentence:
    doc: Document
    idx: int
    start_char: int
    end_char: int
    bow: Counter
    bow_tf_isf: dict

    def __eq__(self, other):
        if type(other) is type(self):
            return self.doc == other.doc and self.start_char == other.start_char
        return False

    def __hash__(self):
        return hash((self.doc, self.idx))
