from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtWidgets import QWidget
from typing import Any, Optional

from data_preprocessor.operation import Operation
from data_preprocessor.operation.Pipeline import Pipeline


class PipelineModel(QAbstractTableModel):
    def __init__(self, pipeline: Pipeline, parent: QWidget = None):
        super().__init__(parent)
        # Reference to the pipeline
        self.__pipeline = pipeline

    def rowCount(self, parent: QModelIndex = ...) -> int:
        if parent.isValid():
            return 0
        return len(self.__pipeline)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        if parent.isValid():
            return 0
        return 1

    def data(self, index: QModelIndex, role: int = ...) -> Optional[Operation]:
        if not index.isValid():
            return None

        if index.column() == 0 and role == Qt.DisplayRole:
            return self.__pipeline[index.row()]

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if index.isValid() and role == Qt.EditRole and index.column() == 0:
            self.__pipeline[index.row()].setOptions(value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return 'Operations'
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return Qt.ItemIsEnabled | Qt.ItemIsEditable
