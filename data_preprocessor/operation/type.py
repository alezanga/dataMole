from typing import List, Union, Iterable, Optional

from PySide2.QtWidgets import QWidget

import data_preprocessor.gui.editor.optionwidget as opw
from data_preprocessor import data
from data_preprocessor.data.types import Types, inv_type_dict
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface import GraphOperation


class ToNumericOp(GraphOperation):
    def __init__(self):
        super().__init__()
        self.__attribute: Optional[int] = None

    def hasOptions(self) -> bool:
        if self.__attribute is not None:
            return True
        return False

    def execute(self, df: data.Frame) -> data.Frame:
        # If type of attribute is not accepted
        if df.shape.col_types[self.__attribute] not in self.acceptedTypes():
            return df
        # Deep copy
        raw_df = df.getRawFrame().copy(deep=True)
        raw_df.iloc[:, [self.__attribute]] = raw_df.iloc[:, [self.__attribute]].astype(
            dtype=inv_type_dict[Types.Numeric], copy=False, errors='raise')
        return data.Frame(raw_df)

    @staticmethod
    def name() -> str:
        return 'toNumeric'

    def shortDescription(self) -> str:
        return 'Convert one attribute to Numeric values. All types except Datetime can be converted'

    def acceptedTypes(self) -> List[Types]:
        return [Types.String, Types.Categorical]

    def setOptions(self, attribute_index: Optional[int]) -> None:
        self.__attribute = attribute_index

    def unsetOptions(self) -> None:
        self.__attribute = None

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return [self.__attribute]

    def getEditor(self) -> AbsOperationEditor:
        return _SelectAttribute()

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions() or not self._shape[0]:
            return None
        # If type of attribute is not accepted
        if self._shape[0].col_types[self.__attribute] not in self.acceptedTypes():
            return self._shape[0]
        s = self._shape[0].copy()
        s.col_types[self.__attribute] = Types.Numeric
        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

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


class ToCategoricalOp(GraphOperation):
    def __init__(self):
        super().__init__()
        self.__attribute: Optional[int] = None

    def hasOptions(self) -> bool:
        if self.__attribute is not None:
            return True
        return False

    def execute(self, df: data.Frame) -> data.Frame:
        # If type of attribute is not accepted
        if df.shape.col_types[self.__attribute] not in self.acceptedTypes():
            return df
        # Deep copy
        raw_df = df.getRawFrame().copy(deep=True)
        raw_df.iloc[:, [self.__attribute]] = raw_df.iloc[:, [self.__attribute]].astype(
            dtype=inv_type_dict[Types.Categorical], copy=False, errors='raise')
        return data.Frame(raw_df)

    @staticmethod
    def name() -> str:
        return 'toCategory'

    def shortDescription(self) -> str:
        return 'Convert one attribute to categorical type. Every different value will be considered a ' \
               'new category'

    def acceptedTypes(self) -> List[Types]:
        return [Types.String, Types.Numeric]

    def setOptions(self, attribute_index: Optional[int]) -> None:
        self.__attribute = attribute_index

    def unsetOptions(self) -> None:
        self.__attribute = None

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return [self.__attribute]

    def getEditor(self) -> AbsOperationEditor:
        return _SelectAttribute()

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions() or not self._shape[0]:
            return None
        # If type is not accepted
        if self._shape[0].col_types[self.__attribute] not in self.acceptedTypes():
            return self._shape[0]
        s = self._shape[0].copy()
        s.col_types[self.__attribute] = Types.Categorical
        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

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


class _SelectAttribute(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        self.__selection_box = opw.AttributeComboBox(self._inputShapes[0], self._acceptedTypes,
                                                     parent=self)
        return self.__selection_box

    def getOptions(self) -> List[Optional[int]]:
        return [self.__selection_box.getData()]

    def setOptions(self, selected_index: Optional[int]) -> None:
        self.__selection_box.setData(selected_index)


# class TypeOp(GraphOperation):
#     def __init__(self):
#         super().__init__()
#         self.__types: Dict[int, Types] = dict()
#
#     def execute(self, df: data.Frame) -> data.Frame:
#         """ Changes type """
#         # Deep copy
#         raw_df = df.getRawFrame().copy(deep=True)
#         colnames = df.colnames
#         for k, v in self.__types.items():
#             # Change type in-place (since raw_df is a deep copy)
#             raw_df[colnames[k]] = raw_df[colnames[k]].astype(dtype=inv_type_dict[v], copy=True,
#                                                              errors='raise')
#         return data.Frame(raw_df)
#
#     @staticmethod
#     def name() -> str:
#         return 'Change column type'
#
#     def info(self) -> str:
#         return 'Change type of data columns'
#
#     def acceptedTypes(self) -> List[Types]:
#         return ALL_TYPES
#
#     def setOptions(self, new_types: Dict[int, Types]) -> None:
#         self.__types = new_types
#
#     def unsetOptions(self) -> None:
#         self.__types = dict()
#
#     def getOptions(self) -> Any:
#         return copy.deepcopy(self.__types), self._shape[0].copy()
#
#     def needsOptions(self) -> bool:
#         return True
#
#     def getEditor(self) -> AbsOperationEditor:
#         pass
#
#     def getOutputShape(self) -> Union[data.Shape, None]:
#         if not self.__types:
#             return copy.deepcopy(self._shape[0])
#         s = copy.deepcopy(self._shape[0])
#         for k, v in self.__types.items():
#             s.col_types[k] = v
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


export = [ToNumericOp, ToCategoricalOp]
