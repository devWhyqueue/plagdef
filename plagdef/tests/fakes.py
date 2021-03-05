from plagdef.algorithm import Document
from plagdef.model import DocumentPairReport


class DocumentPairReportFakeRepository:
    def __init__(self):
        self._doc_pair_reports = []

    def add(self, report: DocumentPairReport):
        self._doc_pair_reports.append(report)

    def list(self) -> list[DocumentPairReport]:
        return self._doc_pair_reports


class DocumentFakeRepository:
    def __init__(self, documents: list[Document]):
        self._documents = documents

    def list(self) -> list[Document]:
        return self._documents


class ConfigFakeRepository:
    def __init__(self, config: dict):
        self._config = config

    def get(self) -> dict:
        return self._config
