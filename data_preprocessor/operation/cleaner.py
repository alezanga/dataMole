from typing import Iterable, Dict, Any, List, Optional

from data_preprocessor import data
from data_preprocessor.gui import AbsOperationEditor, OptionsEditorFactory
from data_preprocessor.gui.mainmodels import FrameModel
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.graph import GraphOperation
from tests.utilities import numpy_equal


def find_duplicates(df):
    groups = df.columns.to_series().groupby(df.dtypes).groups
    duplicates = list()

    for t, v in groups.items():
        cs = df[v].columns
        vs = df[v]
        lcs = len(cs)
        for i in range(lcs):
            ia = vs.iloc[:, i].values
            for j in range(i + 1, lcs):
                ja = vs.iloc[:, j].values
                if numpy_equal(ia, ja):
                    duplicates.append(cs[j])
                    break
    return duplicates


class RemoveBijections(GraphOperation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__selected: List[int] = list()

    def execute(self, df: data.Frame) -> data.Frame:
        df = df.getRawFrame()

        duplicates = find_duplicates(df)

        if duplicates:
            df = df.copy(True)
            df = df.drop(duplicates, axis=1)
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
