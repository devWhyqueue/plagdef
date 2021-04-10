from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from plagdef.model.models import DocumentPairMatches


@dataclass(frozen=True)
class ResultRow:
    doc1: str
    doc1_start_char: int
    doc1_end_char: int
    doc2: str
    doc2_start_char: int
    doc2_end_char: int


class ResultsTableModel(QAbstractTableModel):
    def __init__(self, matches: list[DocumentPairMatches]):
        super().__init__()
        self._rows = []
        for doc_pair_matches in matches:
            for match in doc_pair_matches.list():
                frag1, frag2 = match.frag_pair
                self._rows.append(ResultRow(frag1.doc.name, frag1.start_char, frag1.end_char,
                                            frag2.doc.name, frag2.start_char, frag2.end_char))

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        headers = ['Document 1', 'Start', 'End', 'Document 2', 'Start', 'End']
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return headers[section]

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 6

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        match = self._rows[index.row()]
        match_attributes = [match.doc1, match.doc1_start_char, match.doc1_end_char,
                            match.doc2, match.doc2_start_char, match.doc2_end_char]
        if role == Qt.DisplayRole:
            return match_attributes[index.column()]
        elif role == Qt.ForegroundRole:
            return QColor(255, 255, 255)
