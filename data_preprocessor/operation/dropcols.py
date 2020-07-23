from typing import List, Dict, Optional

from data_preprocessor import data, exceptions as exp
from data_preprocessor.data.types import Type
from data_preprocessor.gui.editor import AbsOperationEditor, OptionsEditorFactory
from data_preprocessor.gui.mainmodels import FrameModel
from data_preprocessor.operation.interface.graph import GraphOperation


class Drop(GraphOperation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # List of selected attributes by column name
        self.__selected: List[str] = list()

    def execute(self, df: data.Frame) -> data.Frame:
        return data.Frame(df.getRawFrame().drop(columns=self.__selected))

    @staticmethod
    def name() -> str:
        return 'DropColumns'

    def setOptions(self, selected: Dict[int, None]) -> None:
        if not selected:
            raise exp.OptionValidationError([('e', 'Error: no attribute is selected')])
        self.__selected = [self.shapes[0].colNames[i] for i in selected.keys()]

    @staticmethod
    def shortDescription() -> str:
        return 'Remove entire columns from dataframe'

    def hasOptions(self) -> bool:
        return bool(self.__selected)

    def unsetOptions(self) -> None:
        self.__selected = list()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Dict[str, Dict[int, None]]:
        return {'selected': {k: None for k in self.__selected}}

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable(key='selected', checkbox=True, nameEditable=False, showTypes=True,
                                   options=None, types=self.acceptedTypes())
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.inputShapes = self.shapes
        editor.workbench = self.workbench
        editor.selected.setSourceFrameModel(FrameModel(editor, self.shapes[0]))

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions():
            return None
        s = self.shapes[0].clone()
        colDict: Dict[str, Type] = s.columnsDict
        s.colNames = [c for c in s.colNames if c not in self.__selected]
        s.colTypes = [t for c, t in colDict.items() if c not in self.__selected]
        return s

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


export = Drop
