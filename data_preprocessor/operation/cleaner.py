from typing import Iterable, Dict, Any, List, Optional

import pandas as pd
import prettytable as pt

from data_preprocessor import data, flogging
from data_preprocessor.gui.editor import AbsOperationEditor, OptionsEditorFactory
from data_preprocessor.gui.mainmodels import FrameModel
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.graph import GraphOperation
from tests.utilities import numpy_equal


def find_duplicates(df: pd.DataFrame) -> List[str]:
    # Convert categories to str
    catTypes: List[str] = df.select_dtypes(include='category').columns.to_list()
    notCat: List[str] = df.select_dtypes(exclude='category').columns.to_list()

    if catTypes:
        copy_df = df[catTypes].astype(object)
        copy_df = pd.concat([copy_df, df[notCat]], axis=1)
    else:
        copy_df = df

    groups = copy_df.columns.to_series().groupby(copy_df.dtypes).groups
    duplicates = list()

    for t, v in groups.items():
        cs = copy_df[v].columns
        vs = copy_df[v]
        lcs = len(cs)
        for i in range(lcs):
            ia = vs.iloc[:, i].values
            for j in range(i + 1, lcs):
                ja = vs.iloc[:, j].values
                if numpy_equal(ia, ja):
                    duplicates.append(cs[j])
                    break
    return duplicates


class RemoveBijections(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__selected: List[int] = list()

    def logOptions(self) -> str:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Selected columns'])
        for a in self.__selected:
            tt.add_row([columns[a]])
        return tt.get_string(vrules=pt.ALL, border=True)

    def execute(self, df: data.Frame) -> data.Frame:
        df = df.getRawFrame()
        colOrder: List[str] = df.columns.to_list()

        subDf = df.iloc[:, self.__selected]

        duplicates = find_duplicates(subDf)

        if duplicates:
            df = df.copy(True)
            df = df.drop(duplicates, axis=1)
            # Keep original order
            order = [c for c in colOrder if c not in duplicates]
            df = df[order]
        return data.Frame(df)

    @staticmethod
    def name() -> str:
        return 'Remove bijections'

    def shortDescription(self) -> str:
        return 'Removes columns with the same values but with different names. Only selected columns ' \
               'will be considered for removal. Match is always performed over all columns'

    def hasOptions(self) -> bool:
        return bool(self.__selected)

    def unsetOptions(self) -> None:
        self.__selected = list()

    def needsOptions(self) -> bool:
        return True

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return False

    @staticmethod
    def needsInputShapeKnown() -> bool:
        return True

    def getOutputShape(self) -> Optional[data.Shape]:
        return None

    def getOptions(self) -> Iterable:
        options = {k: None for k in self.__selected}
        return {'attributes': options}

    def setOptions(self, attributes: Dict[int, Dict[str, Any]]) -> None:
        selection = list(attributes.keys())
        if not selection:
            raise OptionValidationError([('noOptions', 'Error: no attributes are selected')])
        self.__selected = selection

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, False, None, None)
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.acceptedTypes = self.acceptedTypes()
        editor.workbench = self.workbench
        editor.attributes.setSourceFrameModel(FrameModel(editor, self.shapes[0]))

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


export = RemoveBijections
