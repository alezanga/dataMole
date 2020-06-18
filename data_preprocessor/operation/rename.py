import copy
from typing import Union, Dict, List, Any

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtWidgets import QWidget

from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.graph import GraphOperation
from ..gui.mainmodels import AttributeTableModel, FrameModel, SearchableAttributeTableWidget


class RenameOp(GraphOperation):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dict with format {pos: new_name}
        self.__names: Dict[int, str] = dict()

    def execute(self, df: data.Frame) -> data.Frame:
        """ Set new names for columns """

        if not self.__names:
            return df

        names: List[str] = df.colnames
        for k, v in self.__names.items():
            names[k] = v
        new_df = df.getRawFrame().copy(deep=False)
        new_df.columns = names
        return data.Frame(new_df)

    @staticmethod
    def name() -> str:
        return 'Rename operation'

    def shortDescription(self) -> str:
        return 'This operation can rename the attributes'

    def hasOptions(self) -> bool:
        return bool(self.__names)

    def getOptions(self) -> List[Dict[int, str]]:
        return [copy.deepcopy(self.__names)]

    def setOptions(self, names: Dict[int, str]) -> None:
        self.__names = names

    def unsetOptions(self) -> None:
        self.__names = dict()

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        return _RenameEditor()

    def injectEditor(self, editor: '_RenameEditor') -> None:
        editor.inputShapes = self.shapes
        editor.refresh()

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions():
            return None

        # Shape is the same as before with name changed
        s = copy.deepcopy(self._shapes[0])
        for index, name in self.__names.items():
            s.col_names[index] = name

        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    @staticmethod
    def minInputNumber() -> int:
        return 1

    @staticmethod
    def maxInputNumber() -> int:
        return 1

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1


export = RenameOp


class _EditableAttributeTable(AttributeTableModel):
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

        name, col_type = self._frameModel.headerData(index.row(), orientation=Qt.Horizontal,
                                                     role=FrameModel.DataRole.value)
        if index.column() == self.nameColumn:
            # Gets updated value or None
            new_name: str = self._edits.get(index.row(), None)
            # If attribute name was edited before
            if new_name:
                if role == Qt.DisplayRole:
                    return name + ' -> ' + new_name
                elif role == Qt.EditRole:
                    return new_name
            elif role == Qt.DisplayRole or role == Qt.EditRole:
                return name
        else:
            return super().data(index, role)

    def setData(self, index: QModelIndex, value: str, role: int = ...) -> bool:
        if not index.isValid():
            return False

        value = value.strip()
        if role == Qt.EditRole and value and index.column() == self.nameColumn and value != index.data(
                Qt.DisplayRole):
            # TODO: add regex validator
            self._edits[index.row()] = value
        else:
            return False
        self.dataChanged.emit(index, index)
        return True


class _RenameEditor(AbsOperationEditor):
    def getOptions(self) -> List[Dict[int, str]]:
        return [self.__model.editedAttributes()]

    def setOptions(self, option: Dict[int, str]) -> None:
        self.__model.setEditedAttributes(option)

    def editorBody(self) -> QWidget:
        self.__model = _EditableAttributeTable(self)
        self.searchableView = SearchableAttributeTableWidget(checkable=False, editable=True)
        return self.searchableView

    def refresh(self) -> None:
        frame = data.Frame.fromShape(self.inputShapes[0]) if self.inputShapes[0] else data.Frame()
        self.__model.setFrameModel(FrameModel(self, frame))
        self.searchableView.setAttributeModel(self.__model)
