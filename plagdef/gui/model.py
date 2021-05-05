from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from plagdef.model import models
from plagdef.model.models import MatchType
from plagdef.model.util import truncate


@dataclass(frozen=True)
class DocumentPairMatches:
    doc1: models.Document
    doc2: models.Document
    matches: list[models.Match]

    def __len__(self):
        return len(self.matches)


class ResultsTableModel(QAbstractTableModel):
    def __init__(self, match_type: MatchType, doc_pair_matches: list[models.DocumentPairMatches]):
        super().__init__()
        self._doc_pair_matches = []
        for matches in doc_pair_matches:
            typed_matches = matches.list(match_type)
            if len(typed_matches):
                self._doc_pair_matches.append(
                    DocumentPairMatches(matches.doc1, matches.doc2,
                                        sorted(typed_matches,
                                               key=lambda m, doc1=matches.doc1: m.frag_from_doc(doc1).start_char)))

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        headers = ['Document 1', 'Document 2']
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return headers[section]

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._doc_pair_matches)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        doc_pair = self._doc_pair_matches[index.row()].doc1, self._doc_pair_matches[index.row()].doc2
        if role == Qt.DisplayRole:
            name = doc_pair[index.column()].name
            return truncate(name, 50)
        elif role == Qt.ForegroundRole:
            return QColor(255, 255, 255)
        elif role == Qt.ToolTipRole:
            return doc_pair[index.column()].path

    def doc_pair_matches(self, index: QModelIndex) -> DocumentPairMatches:
        return self._doc_pair_matches[index.row()]
