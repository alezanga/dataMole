from typing import Any

from data_preprocessor import data
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation import InputOperation


class CopyOp(InputOperation):
    def __init__(self):
        super().__init__()
        self._worbench_id: int = None

    def execute(self, input) -> data.Frame:
        """ Get selected dataframe from workbench """
        return self._workbench.get(self._worbench_id)

    def name(self) -> str:
        return 'Copy operation'

    def info(self) -> str:
        return 'Copy existing dataframe. Should be used as first operation in a pipeline'

    def setOptions(self, *args, **kwargs) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass
