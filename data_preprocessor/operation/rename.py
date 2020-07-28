import copy
from typing import Union, Dict, List, Any

import prettytable as pt
from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtWidgets import QWidget

from data_preprocessor import data, flogging
from data_preprocessor import exceptions as exp
from data_preprocessor.data.types import ALL_TYPES, Type
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.graph import GraphOperation
from ..gui.mainmodels import AttributeTableModel, FrameModel, SearchableAttributeTableWidget


class RenameColumns(GraphOperation, flogging.Loggable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dict with format {pos: new_name}
        self.__names: Dict[int, str] = dict()

    def logOptions(self) -> str:
        colnames = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Column', 'Renamed column'])
        tt.align = 'l'
        for a, name in self.__names.items():
            tt.add_row([colnames[a], name])
        return tt.get_string(vrules=pt.ALL, border=True)

    def execute(self, df: data.Frame) -> data.Frame:
        """ Set new names for columns """
        names: List[str] = df.colnames
        for k, v in self.__names.items():
            names[k] = v
        new_df = df.getRawFrame().copy(deep=False)
        new_df.columns = names
        return data.Frame(new_df)

    @staticmethod
    def name() -> str:
        return 'Rename columns'

    @staticmethod
    def shortDescription() -> str:
        return 'This operation can rename the attributes'

    def hasOptions(self) -> bool:
        return bool(self.__names)

    def getOptions(self) -> List[Dict[int, str]]:
        return [copy.deepcopy(self.__names)]

    def setOptions(self, names: Dict[int, str]) -> None:
        # Compute the output shape
        s = self._shapes[0]
        if s:
            s = s.clone()
            for index, name in self.__names.items():
                s.colNames[index] = name
            if len(set(s.colNames)) < s.nColumns:
                raise exp.OptionValidationError([('dup', 'Error: new names contain duplicates')])
        self.__names = copy.deepcopy(names)

    def unsetOptions(self) -> None:
        self.__names = dict()

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        return RenameEditor()

    def injectEditor(self, editor: 'RenameEditor') -> None:
        editor.refresh()

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions() or not self.shapes[0]:
            return None

        # Shape is the same as before with name changed
        s = self._shapes[0].clone()
        for index, name in self.__names.items():
            s.colNames[index] = name

        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    def acceptedTypes(self) -> List[Type]:
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


# class RenameIndex(GraphOperation, flogging.Loggable):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Dict with format {pos: new_name}
#         self.__names: Dict[int, str] = dict()
#
#     def execute(self, df: data.Frame) -> data.Frame:
#         names: List[str] = df.shape.index
#         for k, v in self.__names.items():
#             names[k] = v
#         new_df = df.getRawFrame().copy(deep=False)
#         new_df.index.names = names
#         return data.Frame(new_df)
#
#     @staticmethod
#     def name() -> str:
#         return 'RenameIndex'
#
#     @staticmethod
#     def shortDescription() -> str:
#         return 'Rename index levels'
#
#     def getOptions(self) -> List[Dict[int, str]]:
#         return [copy.deepcopy(self.__names)]
#
#     def setOptions(self, names: Dict[int, str]) -> None:
#         s = self.getOutputShape()
#         if s and len(set(s.index)) < s.nIndexLevels:
#             raise exp.OptionValidationError([('dup', 'Error: new names contain duplicates')])
#         self.__names = copy.deepcopy(names)
#
#     def unsetOptions(self) -> None:
#         self.__names = dict()
#
#     def needsOptions(self) -> bool:
#         return True
#
#     def hasOptions(self) -> bool:
#         return bool(self.__names)
#
#     def getEditor(self) -> AbsOperationEditor:
#         return IndexRenameEditor()
#
#     def injectEditor(self, editor: 'IndexRenameEditor') -> None:
#         editor.refresh()
#
#     def getOutputShape(self) -> Union[data.Shape, None]:
#         if not self.hasOptions() or not self.shapes[0]:
#             return None
#         # Shape is the same as before with index names changed
#         s = self._shapes[0].clone()
#         for index, name in self.__names.items():
#             s.index[index] = name
#         return s
#
#     @staticmethod
#     def isOutputShapeKnown() -> bool:
#         return True
#
#     @staticmethod
#     def minInputNumber() -> int:
#         return 1
#
#     @staticmethod
#     def maxInputNumber() -> int:
#         return 1
#
#     @staticmethod
#     def minOutputNumber() -> int:
#         return 1
#
#     @staticmethod
#     def maxOutputNumber() -> int:
#         return -1


export = RenameColumns


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
                                                     role=FrameModel.DataRole)
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
        if role == Qt.EditRole and value and index.column() == self.nameColumn and \
                value != index.data(Qt.EditRole):
            # TODO: add regex validator
            self._edits[index.row()] = value
        else:
            return False
        self.dataChanged.emit(index, index)
        return True


class RenameEditor(AbsOperationEditor):
    def getOptions(self) -> List[Dict[int, str]]:
        return [self._model.editedAttributes()]

    def setOptions(self, option: Dict[int, str]) -> None:
        self._model.setEditedAttributes(option)

    def editorBody(self) -> QWidget:
        self._model = _EditableAttributeTable(self)
        self.searchableView = SearchableAttributeTableWidget(checkable=False, editable=True)
        return self.searchableView

    def refresh(self) -> None:
        frame = data.Frame.fromShape(self.inputShapes[0]) if self.inputShapes[0] else data.Frame()
        self._model.setFrameModel(FrameModel(self, frame))
        self.searchableView.setAttributeModel(self._model)

# class IndexRenameEditor(RenameEditor):
#     def refresh(self) -> None:
#         frame = data.Frame.fromShape(self.inputShapes[0]) if self.inputShapes[0] else data.Frame()
#         df = frame.getRawFrame()
#         # Rename index in dummy frame
#         df.index.names = [n if n else '' for n in df.index.names]
#         indexFrame = df.index.to_frame(index=False)
#         self._model.setFrameModel(FrameModel(self, indexFrame))
#         self.searchableView.setAttributeModel(self._model)
