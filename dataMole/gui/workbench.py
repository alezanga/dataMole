# -*- coding: utf-8 -*-
#
# Author:       Alessandro Zangari (alessandro.zangari.code@outlook.com)
# Copyright:    © Copyright 2020 Alessandro Zangari, Università degli Studi di Padova
# License:      GPL-3.0-or-later
# Date:         2020-10-04
# Version:      1.0
#
# This file is part of DataMole.
#
# DataMole is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# DataMole is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DataMole.  If not, see <https://www.gnu.org/licenses/>.

from typing import Any, List, Optional, Dict

from PySide2 import QtGui
from PySide2.QtCore import QAbstractListModel, QObject, QModelIndex, Qt, Slot, Signal, QItemSelection, \
    QItemSelectionModel
from PySide2.QtWidgets import QListView, QTableView, QHeaderView

import dataMole.data as d
from dataMole.gui.mainmodels import FrameModel

_EMPTY_ROW_NAME = ' '


class WorkbenchModel(QAbstractListModel):
    emptyRowInserted = Signal(QModelIndex)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.__workbench: List[FrameModel] = list()
        self.__nameToIndex: Dict[str, int] = dict()

    @property
    def modelList(self) -> List[FrameModel]:
        return self.__workbench

    @property
    def modelDict(self) -> Dict[str, FrameModel]:
        return {n: self.__workbench[i] for n, i in self.__nameToIndex.items()}

    @property
    def names(self) -> List[str]:
        return list(self.__nameToIndex.keys())

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.__workbench)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[str]:
        """ Show the name of the dataframe """
        if not index.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.__workbench[index.row()].name
        else:
            return None

    def setData(self, index: QModelIndex, newName: str, role: int = Qt.EditRole) -> bool:
        """ Change name of dataframe """
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            newName = newName.strip()
            oldName = self.data(index, Qt.DisplayRole)
            if not newName or newName == oldName or newName in self.names:
                # Name is empty string, value is unchanged or the name already exists
                if oldName == _EMPTY_ROW_NAME:
                    # Then a dummy entry was set and must be deleted, since user didn't provide a
                    # valid name
                    self.removeRow(index.row())
                return False  # No changes
            # Edit entry with the new name and the old value
            self.__workbench[index.row()].name = newName
            self.__nameToIndex[newName] = self.__nameToIndex.pop(oldName)
            # Update view
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    def getDataframeModelByIndex(self, index: int) -> FrameModel:
        return self.__workbench[index]

    def getDataframeModelByName(self, name: str) -> FrameModel:
        return self.__workbench[self.__nameToIndex[name]]

    def setDataframeByName(self, name: str, value: d.Frame) -> bool:
        listPos: int = self.__nameToIndex.get(name, None)
        if listPos is not None:
            # Name already exists
            if self.__workbench[listPos].frame is value:
                return False
            frame_model = self.getDataframeModelByIndex(listPos)
            # This will reset any view currently showing the frame
            frame_model.setFrame(value)
            self.__workbench[listPos] = frame_model
            # nameToIndex is already updated (no change)
            # dataChanged is not emitted because the frame name has not changed
        else:
            # Name does not exists, so add as a new row
            row = self.rowCount()
            f = FrameModel(None, value)  # No parent is set
            f.name = name
            self.beginInsertRows(QModelIndex(), row, row)
            self.__workbench.append(f)
            self.__nameToIndex[name] = row
            self.endInsertRows()
        return True

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
        # Recreate updated dictionary
        self.__nameToIndex = {name: (i if i < row else i - 1)
                              for name, i in self.__nameToIndex.items() if i != row}
        self.endRemoveRows()
        return True

    @Slot()
    def appendEmptyRow(self) -> bool:
        row = self.rowCount()
        # Create a dummy entry
        f = FrameModel()
        f.name = _EMPTY_ROW_NAME
        self.beginInsertRows(QModelIndex(), row, row)
        self.__workbench.append(f)
        self.__nameToIndex[f.name] = row
        self.endInsertRows()
        self.emptyRowInserted.emit(self.index(row, 0, QModelIndex()))
        return True


class WorkbenchView(QTableView):
    selectedRowChanged = Signal((int, int), (str, str))
    rightClick = Signal(QModelIndex)

    def __init__(self, parent=None, editable: bool = True):
        super().__init__(parent)
        self.setSelectionMode(QListView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)

        # Allow rearrange of rows
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionsMovable(True)
        self.verticalHeader().setDragEnabled(True)
        self.verticalHeader().setDragDropMode(QHeaderView.InternalMove)
        self.verticalHeader().setDragDropOverwriteMode(False)
        self.verticalHeader().setDropIndicatorShown(True)
        self.verticalHeader().hide()
        self._editable = editable
        if not self._editable:
            self.setEditTriggers(QListView.NoEditTriggers)

    @Slot(QModelIndex)
    def startEditNoSelection(self, index: QModelIndex) -> None:
        """ Start editing a row without changing the selection """
        self.selectionModel().setCurrentIndex(index, QItemSelectionModel.NoUpdate)
        self.edit(index)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Delete and self._editable:
            for index in self.selectedIndexes():
                self.model().removeRow(index.row())
        else:
            super().keyPressEvent(event)

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        """ Emit signal when current selection changes """
        super().selectionChanged(selected, deselected)
        current: QModelIndex = selected.indexes()[0] if selected.indexes() else QModelIndex()
        previous: QModelIndex = deselected.indexes()[0] if deselected.indexes() else QModelIndex()
        currRow: int = -1
        prevRow: int = -1
        currName: str = ''
        prevName: str = ''
        if current.isValid():
            currRow = current.row()
            currName = current.data(Qt.DisplayRole)
        if previous.isValid():
            prevRow = previous.row()
            prevName = previous.data(Qt.DisplayRole)
        self.selectedRowChanged[int, int].emit(currRow, prevRow)
        self.selectedRowChanged[str, str].emit(currName, prevName)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)
        if self._editable:
            self.verticalHeader().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        if self._editable:
            self.verticalHeader().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self._editable:
            self.verticalHeader().mouseReleaseEvent(event)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        index: QModelIndex = self.indexAt(event.pos())
        if index.isValid():
            self.rightClick.emit(index)
