from typing import Any, List

from PySide2.QtCore import QAbstractListModel, QObject, QModelIndex, Qt, Slot, Signal

from data_preprocessor.data.Workbench import Workbench
import data_preprocessor.data as d


class WorkbenchModel(QAbstractListModel):
    rowAppended = Signal(QModelIndex)

    def __init__(self, parent: QObject = None, workbench: Workbench = Workbench()):
        super().__init__(parent)
        self._workbench = workbench
        self._index_list: List[str] = list()
        for k in self._workbench.keys():
            self._index_list.append(k)

        # Whenever a row is inserted slot is called to emit the signal
        self.rowsInserted.connect(self.__endAppendRow)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._index_list)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._index_list[index.row()]  # The name of the variable
        else:
            return None

    def setData(self, index: QModelIndex, value: str, role: int = ...) -> bool:
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            value = value.strip()
            if not value or value == self.data(index, Qt.DisplayRole) or value in self._workbench.keys():
                # Name is empty string, value is unchanged or the name already exists
                if self.data(index, Qt.DisplayRole) == ' ':
                    # Then a dummy entry was set and must be deleted, since user didn't provide a
                    # valid name
                    self.removeRow(index.row())
                return False  # No changes
            # Add a new entry with the new name and the old value
            self._workbench[value] = self._workbench[self.data(index, Qt.DisplayRole)]
            # Delete old entry
            del self._workbench[self.data(index, Qt.DisplayRole)]
            # Update mapping with index now pointing to new name
            self._index_list[index.row()] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if section != 0 or orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None
        return 'Dataframes'

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        if not 0 <= row < self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row)
        del self._workbench[self._index_list[row]]
        del self._index_list[row]  # rows naturally scale
        self.endRemoveRows()
        return True

    def getVariable(self, name: str) -> d.Frame:
        return self._workbench[name]

    @Slot()
    def appendRow(self) -> bool:
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        # Create a dummy entry
        self._workbench[' '] = d.Frame()
        # Add to the end of the list
        self._index_list.append(' ')
        self.endInsertRows()
        return True

    @Slot(QModelIndex, int, int)
    def __endAppendRow(self, parent, first, last) -> None:
        self.rowAppended.emit(self.index(first, 0, parent))
