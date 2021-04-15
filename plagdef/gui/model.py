from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from plagdef.model import models


@dataclass(frozen=True)
class ResultRow:
    doc1: str
    doc2: str


@dataclass(frozen=True)
class DocumentPairMatches:
    doc1: models.Document
    doc2: models.Document
    matches: list[models.Match]

    def __len__(self):
        return len(self.matches)


class ResultsTableModel(QAbstractTableModel):
    def __init__(self, doc_pair_matches: set[models.DocumentPairMatches]):
        super().__init__()
        self._rows = []
        self._doc_pair_matches = []
        for matches in doc_pair_matches:
            doc1, doc2 = matches.doc_pair
            self._rows.append(ResultRow(doc1.name, doc2.name))
            self._doc_pair_matches.append(
                DocumentPairMatches(doc1, doc2, sorted(matches.list(), key=lambda m: m.frag_from_doc(doc1).start_char)))

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        headers = ['Document 1', 'Document 2']
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return headers[section]

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        doc_pair = self._rows[index.row()]
        doc_pair_attributes = [doc_pair.doc1, doc_pair.doc2]
        if role == Qt.DisplayRole:
            return doc_pair_attributes[index.column()]
        elif role == Qt.ForegroundRole:
            return QColor(255, 255, 255)

    def doc_pair_matches(self, index: QModelIndex) -> DocumentPairMatches:
        return self._doc_pair_matches[index.row()]
