from typing import Any, List, Tuple, Optional

from PySide2 import QtGui
from PySide2.QtCore import QAbstractListModel, QObject, QModelIndex, Qt, Slot, Signal, QItemSelection
from PySide2.QtWidgets import QListView, QTableView, QHeaderView

import data_preprocessor.data as d
from data_preprocessor.gui.frame import FrameModel


class WorkbenchModel(QAbstractListModel):
    emptyRowInserted = Signal(QModelIndex)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.__workbench: List[Tuple[str, FrameModel]] = list()

    @property
    def keys(self) -> List[str]:
        return [a[0] for a in self.__workbench]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.__workbench)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[str]:
        """ Show the name of the dataframe """
        if not index.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.__workbench[index.row()][0]
        else:
            return None

    def setData(self, index: QModelIndex, new_name: str, role: int = Qt.EditRole) -> bool:
        """ Change name of dataframe """
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            new_name = new_name.strip()
            old_name = self.data(index, Qt.DisplayRole)
            old_model = self.getDataframeModelByIndex(index.row())
            if not new_name or new_name == old_name or new_name in self.keys:
                # Name is empty string, value is unchanged or the name already exists
                if old_name == ' ':
                    # Then a dummy entry was set and must be deleted, since user didn't provide a
                    # valid name
                    self.removeRow(index.row())
                return False  # No changes
            # Edit entry with the new name and the old value
            self.__workbench[index.row()] = (new_name, old_model)
            # Update view
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    def getDataframeByName(self, name: str) -> d.Frame:
        return self.__workbench[[e[0] for e in self.__workbench].index(name)][1].frame

    def getDataframeByIndex(self, index: int) -> d.Frame:
        return self.__workbench[index][1].frame

    def getDataframeModelByIndex(self, index: int) -> FrameModel:
        return self.__workbench[index][1]

    def setDataframeByIndex(self, index: QModelIndex, value: d.Frame) -> bool:
        if not index.isValid():
            return False
        if self.getDataframeByIndex(index.row()) == value:
            return False
        frame_model = self.getDataframeModelByIndex(index.row())
        # This will reset any view currently showing the frame
        frame_model.setFrame(value)
        self.__workbench[index.row()] = (self.data(index, Qt.DisplayRole), frame_model)
        # dataChanged is not emitted because the frame name has not changed

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if section != 0 or orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None
        return 'Workbench'

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        if not 0 <= row < self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row)
        # Update views showing the frame
        frame_model = self.getDataframeModelByIndex(row)
        # Reset connected models by showing an empty frame. This also delete their reference
        frame_model.setFrame(frame=d.Frame())
        # Now delete row
        del self.__workbench[row]
        self.endRemoveRows()
        return True

    @Slot()
    def appendEmptyRow(self) -> bool:
        row = self.rowCount()
        self.beginInsertRows(QModelIndex(), row, row)
        # Create a dummy entry
        self.__workbench.append((' ', FrameModel()))
        self.endInsertRows()
        self.emptyRowInserted.emit(self.index(row, 0, QModelIndex()))
        return True

    def appendNewRow(self, name: str, frame: d.Frame) -> bool:
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        # Create a dummy entry
        self.__workbench.append((name, FrameModel(None, frame)))
        # NOTE: no parent is set
        self.endInsertRows()
        return True


class WorkbenchView(QTableView):
    selectedRowChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)

        # Allow rearrange of rows
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionsMovable(True)
        self.verticalHeader().setDragEnabled(True)
        self.verticalHeader().setDragDropMode(QTableView.InternalMove)
        self.verticalHeader().setDragDropOverwriteMode(False)
        self.verticalHeader().setDropIndicatorShown(True)
        self.verticalHeader().hide()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Delete:
            for index in self.selectedIndexes():
                self.model().removeRow(index.row())
        else:
            super().keyPressEvent(event)

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        """ Emit signal when current selection changes """
        super().selectionChanged(selected, deselected)
        current: QModelIndex = selected.indexes()[0] if selected.indexes() else QModelIndex()
        if current.isValid():
            self.selectedRowChanged.emit(current.row())
        else:
            self.selectedRowChanged.emit(-1)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super().mousePressEvent(event)
        self.verticalHeader().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super().mouseMoveEvent(event)
        self.verticalHeader().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        super().mouseReleaseEvent(event)
        self.verticalHeader().mouseReleaseEvent(event)
