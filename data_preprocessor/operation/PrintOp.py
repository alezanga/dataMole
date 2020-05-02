from typing import Any

from data_preprocessor import data
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from .interface import OutputOperation


class PrintOp(OutputOperation):
    def execute(self, *df: data.Frame) -> None:
        for f in df:
            print(f.head())
            print(f.head().dtypes)

    @staticmethod
    def name() -> str:
        return 'Print operation'

    def info(self) -> str:
        return 'Just prints its input'

    def setOptions(self, *args, **kwargs) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass

    def needsOptions(self) -> bool:
        pass
