from typing import Any

from data_preprocessor import data
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation import OutputOperation


class PrintOp(OutputOperation):
    def execute(self, *df: data.Frame) -> None:
        for f in df:
            print(f.head())
            print(f.head().dtypes)

    def name(self) -> str:
        return 'Print operation'

    def info(self) -> str:
        return 'Just prints its input'

    def setOptions(self, *args, **kwargs) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass
