from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor


@dataclass(frozen=True)
class DocumentPairMatch:
    doc1: str
    doc1_offset: int
    doc1_length: int
    doc2: str
    doc2_offset: int
    doc2_length: int


@dataclass
class Config:
    doc_dir: Path
    lang: str


class ResultsTableModel(QAbstractTableModel):
    def __init__(self, matches: list[DocumentPairMatch]):
        super().__init__()
        self._matches = matches

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        headers = ['Document 1', 'Offset', 'Length', 'Document 2', 'Offset', 'Length']
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return headers[section]

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 6

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._matches)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        match = self._matches[index.row()]
        match_attributes = [match.doc1, match.doc1_offset, match.doc1_length,
                            match.doc2, match.doc2_offset, match.doc2_length]
        if role == Qt.DisplayRole:
            return match_attributes[index.column()]
        elif role == Qt.ForegroundRole:
            return QColor(255, 255, 255)
