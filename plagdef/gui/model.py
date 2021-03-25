from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from plagdef.model.legacy import algorithm


@dataclass(frozen=True)
class ResultRow:
    doc1: str
    doc1_offset: int
    doc1_length: int
    doc2: str
    doc2_offset: int
    doc2_length: int


class ResultsTableModel(QAbstractTableModel):
    def __init__(self, matches: list[algorithm.DocumentPairMatches]):
        super().__init__()
        self._rows = []
        for doc_pair_matches in matches:
            for match in doc_pair_matches.list():
                self._rows.append(ResultRow(doc_pair_matches.doc1.name, match.sec1.offset, match.sec1.length,
                                            doc_pair_matches.doc2.name, match.sec2.offset, match.sec2.length))

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        headers = ['Document 1', 'Offset', 'Length', 'Document 2', 'Offset', 'Length']
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return headers[section]

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 6

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        match = self._rows[index.row()]
        match_attributes = [match.doc1, match.doc1_offset, match.doc1_length,
                            match.doc2, match.doc2_offset, match.doc2_length]
        if role == Qt.DisplayRole:
            return match_attributes[index.column()]
        elif role == Qt.ForegroundRole:
            return QColor(255, 255, 255)
