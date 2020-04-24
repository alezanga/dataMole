from enum import Enum
from typing import Any

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtWidgets import QWidget

from data_preprocessor.data import Frame


# New role to return raw data from header
class MyRoles(Enum):
    DataRole = Qt.UserRole


class FrameModel(QAbstractTableModel):
    """ Table model for a single dataframe """

    DataRole = MyRoles.DataRole

    def __init__(self, parent: QWidget = None, frame: Frame = Frame(), nrows: int = 10):
        super().__init__(parent)
        self._frame: Frame = frame
        self._n_rows: int = nrows

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._frame.shape.n_rows if self._frame.shape.n_rows < self._n_rows else self._n_rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._frame.shape.n_columns

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if index.isValid() and index.row() < self._n_rows:
            if role == Qt.DisplayRole:
                return str(self._frame.at((index.row(), index.column())))
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self._frame.shape.col_names[section] + '\n' + self._frame.shape.col_types[
                    section].value
            elif role == FrameModel.DataRole:
                return self._frame.shape.col_names[section], self._frame.shape.col_types[section].value
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            if self._frame.shape.has_index():
                return self._frame.index[section]
        return None

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = ...) \
            -> bool:
        if orientation == Qt.Horizontal and role == Qt.EditRole and section < self.columnCount():
            names = self._frame.colnames
            names[section] = value
            self._frame = self._frame.rename({self.headerData(section, orientation,
                                                              FrameModel.DataRole)[0]: value})
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return False
