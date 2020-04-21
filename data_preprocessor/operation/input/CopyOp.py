from typing import Any

from data_preprocessor import data
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation import InputOperation


class CopyOp(InputOperation):

    def execute(self, df: data.Frame) -> data.Frame:
        pass

    def name(self) -> str:
        pass

    def info(self) -> str:
        pass

    def setOptions(self, *args, **kwargs) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass
