from typing import Any

from data_preprocessor import data
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.graph import OutputGraphOperation


class PrintOp(OutputGraphOperation):
    def execute(self, *df: data.Frame) -> None:
        for f in df:
            print(f.head())
            print(f.head().dtypes)

    @staticmethod
    def name() -> str:
        return 'Print operation'

    @staticmethod
    def shortDescription() -> str:
        return 'Just prints its input'

    def setOptions(self, *args, **kwargs) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def hasOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        pass

    def needsOptions(self) -> bool:
        pass
