from typing import Dict, Any, List

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtWidgets import QTableView, QHeaderView, QWidget

from data_preprocessor import data
from data_preprocessor.gui.editor import AbsOperationEditor
from ..frame import AttributeTableModel, FrameModel, AttributeTableModelFilter


class EditableAttributeTable(AttributeTableModel):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent, False, True)
        # Keeps track of changes in names for attribute name column
        self._edits: Dict[int, str] = dict()

    def editedAttributes(self) -> Dict[int, str]:
        """ Get attributes that were edited """
        return self._edits.copy()

    def setEditedAttributes(self, e: Dict[int, str]) -> None:
        """ Set the edited attributes in the model and update the view """
        self.beginResetModel()
        self._edits = e
        self.endResetModel()

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return None

        name, col_type = self._sourceModel.headerData(index.row(), orientation=Qt.Horizontal)
        if index.column() == self.name_pos:
            # Gets updated value or None
            new_name: str = self._edits.get(index.row(), None)
            # If attribute name was edited before
            if new_name:
                if role == Qt.DisplayRole:
                    return name + ' -> ' + new_name
                elif role == Qt.EditRole:
                    return new_name
        else:
            return super().data(index, role)

    def setData(self, index: QModelIndex, value: str, role: int = ...) -> bool:
        if not index.isValid():
            return False

        value = value.strip()
        if role == Qt.EditRole and value and index.column() == self.name_pos and value != index.data(
                Qt.DisplayRole):
            # TODO: add regex validator
            self._edits[index.row()] = value
        else:
            return False
        self.dataChanged.emit(index, index)
        return True


class RenameEditor(AbsOperationEditor):
    def getOptions(self) -> List[Dict[int, str]]:
        return [self.__source_model.editedAttributes()]

    def setOptions(self, option: Dict[int, str]) -> None:
        self.__source_model.setEditedAttributes(option)

    def editorBody(self) -> QWidget:
        self.setWindowTitle('Rename operation editor')

        frame = data.Frame.fromShape(self._inputShapes[0]) if self._inputShapes[0] else data.Frame()
        self.__source_model = EditableAttributeTable(self)
        self.__model = AttributeTableModelFilter(filterTypes=self._acceptedTypes, parent=self)
        self.__source_model.setSourceModel(FrameModel(self, frame))
        self.__model.setSourceModel(self.__source_model)
        # View shows filtered model
        self.__view = QTableView(self)
        self.__view.setModel(self.__model)
        header = self.__view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.__view.setHorizontalHeader(header)
        return self.__view
