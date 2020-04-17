from typing import Any

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtWidgets import QWidget

from data_preprocessor.data import Frame


class FrameModel(QAbstractTableModel):
    def __init__(self, parent: QWidget = None, frame: Frame = Frame(), nrows: int = 10):
        super().__init__(parent)
        self._frame = frame
        self._n_rows = nrows

    def rowCount(self, parent: QModelIndex = ...) -> int:
        if parent.isValid():
            return 0
        return self._frame.shape.n_rows

    def columnCount(self, parent: QModelIndex = ...) -> int:
        if parent.isValid():
            return 0
        return self._frame.shape.n_columns

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if index.isValid() and index.row() < self._n_rows:
            if role == Qt.DisplayRole:
                return self._frame[...]
            # TODO
