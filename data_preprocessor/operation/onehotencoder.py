from operator import itemgetter
from typing import Iterable, List, Union, Tuple

import pandas as pd
import prettytable as pt
from PySide2.QtWidgets import QWidget, QCheckBox, QVBoxLayout

from data_preprocessor import data, flogging
from data_preprocessor.data.types import Types, Type
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, FrameModel
from data_preprocessor.operation.interface.graph import GraphOperation


class OneHotEncodeOp(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attributes: List[int] = list()
        self.__includeNan: bool = None

    def logOptions(self) -> None:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Selected columns'])
        for a in self.__attributes:
            tt.add_row([columns[a]])
        tt.align = 'l'
        return tt.get_string(border=True, vrules=pt.ALL) + '\nWith Nan column: {:b}'.format(
            self.__includeNan)

    def execute(self, df: data.Frame) -> data.Frame:
        pdf = df.getRawFrame().copy(deep=True)
        columns = pdf.columns
        prefixes = itemgetter(*self.__attributes)(self.shapes[0].colNames)
        npdf = pd.get_dummies(pdf.iloc[:, self.__attributes], prefix=prefixes,
                              dummy_na=self.__includeNan, dtype=int)
        npdf = npdf.astype('category', copy=False)
        pdf = pdf.drop(columns[self.__attributes], axis=1, inplace=False)
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

    def acceptedTypes(self) -> List[Type]:
        return [Types.Ordinal, Types.Nominal, Types.String]

    def getOptions(self) -> Iterable:
        return self.__attributes, self.__includeNan

    def setOptions(self, attributes: List[int], includeNan: bool) -> None:
        self.__attributes = attributes
        self.__includeNan = includeNan

    def getEditor(self) -> AbsOperationEditor:
        return _SelectAttribute()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.inputShapes = self.shapes
        editor.refresh()

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
        self.__nancol = QCheckBox('Column for nan?', self)
        layout = QVBoxLayout()
        layout.addWidget(self.__searchableTable)
        layout.addWidget(self.__nancol)
        w = QWidget(self)
        w.setLayout(layout)
        return w

    def refresh(self) -> None:
        self.__searchableTable.setSourceFrameModel(FrameModel(self, self.inputShapes[0]))

    def getOptions(self) -> Tuple[List[int], bool]:
        return self.__searchableTable.model().checked, self.__nancol.isChecked()

    def setOptions(self, selected_indexes: List[int], nancol: bool) -> None:
        self.__searchableTable.model().setChecked(selected_indexes, True)
        self.__nancol.setChecked(nancol if nancol is not None else False)


export = OneHotEncodeOp
