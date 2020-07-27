from operator import itemgetter
from typing import List, Union, Dict

import pandas as pd
import prettytable as pt

from data_preprocessor import data, flogging
from data_preprocessor.data.types import Types, Type
from data_preprocessor.gui.editor import AbsOperationEditor, OptionsEditorFactory
from data_preprocessor.gui.mainmodels import FrameModel
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
        prefixes = itemgetter(*self.__attributes)(self.shapes[0].colNames)
        npdf = pd.get_dummies(pdf.iloc[:, self.__attributes], prefix=prefixes,
                              dummy_na=self.__includeNan, dtype=int)
        npdf = npdf.astype('category', copy=False)
        # Replace eventual duplicate columns
        pdf = pdf.drop(columns=npdf.columns, errors='ignore')
        # Avoid dropping original columns (just append)
        # pdf = pdf.drop(columns[self.__attributes], axis=1, inplace=False)
        pdf = pd.concat([pdf, npdf], axis=1)
        return data.Frame(pdf)

    @staticmethod
    def name() -> str:
        return 'One-hot encoder'

    @staticmethod
    def shortDescription() -> str:
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

    def getOptions(self) -> Dict[str, Union[Dict[int, None], bool]]:
        return {
            'attributes': {k: None for k in self.__attributes},
            'includeNan': self.__includeNan
        }

    def setOptions(self, attributes: Dict[int, None], includeNan: bool) -> None:
        self.__attributes = list(attributes.keys())
        self.__includeNan = includeNan

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True, None, self.acceptedTypes())
        factory.withCheckBox('Column for nan', 'includeNan')
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.attributes.setSourceFrameModel(FrameModel(editor, self._shapes[0]))

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


export = OneHotEncodeOp
