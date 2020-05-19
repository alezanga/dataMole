from typing import Union, Any, List

from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from data_preprocessor.operation.interface.graph import GraphOperation


class DummyOp(GraphOperation):
    def __init__(self):
        super().__init__()

    def execute(self) -> None:
        return None

    def name(self) -> str:
        return 'Dummy operation'

    def shortDescription(self) -> str:
        return 'This operation does nothing and returns None'

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def setOptions(self, *args, **kwargs) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def hasOptions(self) -> bool:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass

    def getOutputShape(self) -> Union[data.Shape, None]:
        return self._shape[0]

    def unsetOptions(self) -> None:
        pass

    def needsOptions(self) -> bool:
        pass

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    @staticmethod
    def minInputNumber() -> int:
        return 0

    @staticmethod
    def maxInputNumber() -> int:
        return 0

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1
