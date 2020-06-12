from operator import itemgetter
from typing import Iterable, List, Union, Tuple

import pandas as pd
from PySide2.QtWidgets import QWidget, QCheckBox, QVBoxLayout

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, FrameModel
from data_preprocessor.operation.interface.graph import GraphOperation


class OneHotEncodeOp(GraphOperation):
    def __init__(self):
        super().__init__()
        self.__attributes: List[int] = list()
        self.__includeNan: bool = None

    def execute(self, df: data.Frame) -> data.Frame:
        pdf = df.getRawFrame().copy(deep=True)
        prefixes = itemgetter(*self.__attributes)(self.shapes[0].col_names)
        npdf = pd.get_dummies(pdf.iloc[:, self.__attributes], prefix=prefixes,
                              dummy_na=self.__includeNan, dtype=int)
        npdf = npdf.astype('category', copy=False)
        pdf.drop(pdf.columns[self.__attributes], axis=1, inplace=True)
        pdf = pd.concat([pdf, npdf], axis=1)
        return data.Frame(pdf)

    @staticmethod
    def name() -> str:
        return 'One-hot encoder'

    def shortDescription(self) -> str:
        return 'Replace every categorical value with a binary attribute'

    def longDescription(self) -> str:
        return 'Can be done on categorical or string attributes. The new attribute columns are of ' \
               'categorical type'

    def hasOptions(self) -> bool:
        if self.__attributes and self.__includeNan is not None:
            return True
        return False

    def unsetOptions(self) -> None:
        self.__attributes = list()

    def needsOptions(self) -> bool:
        return True

    def acceptedTypes(self) -> List[Types]:
        return [Types.Categorical, Types.String]

    def getOptions(self) -> Iterable:
        return self.__attributes, self.__includeNan

    def setOptions(self, attributes: List[int], includeNan: bool) -> None:
        self.__attributes = attributes
        self.__includeNan = includeNan

    def getEditor(self) -> AbsOperationEditor:
        return _SelectAttribute()

    def getOutputShape(self) -> Union[data.Shape, None]:
        return None

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return False

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
        self.__searchableTable = SearchableAttributeTableWidget(checkable=True,
                                                                showTypes=True,
                                                                filterTypes=self.acceptedTypes)
        self.__searchableTable.setSourceFrameModel(FrameModel(self, self.inputShapes[0]))
        self.__nancol = QCheckBox('Column for nan?', self)
        layout = QVBoxLayout()
        layout.addWidget(self.__searchableTable)
        layout.addWidget(self.__nancol)
        w = QWidget(self)
        w.setLayout(layout)
        return w

    def getOptions(self) -> Tuple[List[int], bool]:
        return self.__searchableTable.model().checkedAttributes, self.__nancol.isChecked()

    def setOptions(self, selected_indexes: List[int], nancol: bool) -> None:
        self.__searchableTable.model().checkedAttributes = selected_indexes
        self.__nancol.setChecked(nancol if nancol is not None else False)


export = OneHotEncodeOp
