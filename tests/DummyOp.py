from typing import Union, Any, Iterable, Optional, List

from data_preprocessor import data
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from data_preprocessor.operation.interface.graph import GraphOperation, InputGraphOperation, \
    OutputGraphOperation


class InputDummy(InputGraphOperation):
    def __init__(self):
        super().__init__()
        self.__df = None

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions():
            return None
        return self.__df.shape

    def execute(self, *df: data.Frame) -> data.Frame:
        if self.hasOptions():
            return self.__df

    @staticmethod
    def name() -> str:
        return 'Input dummy'

    def shortDescription(self) -> str:
        return 'Accept an input dataframe with options'

    def hasOptions(self) -> bool:
        return self.__df is not None

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return (self.__df,)

    def getEditor(self) -> AbsOperationEditor:
        pass

    def setOptions(self, df: Optional[data.Frame]) -> None:
        self.__df: data.Frame = df


class OutputDummy(OutputGraphOperation):
    def __init__(self):
        super().__init__()
        self.__out = None

    def execute(self, df: data.Frame) -> None:
        self.__out[0] = df

    @staticmethod
    def name() -> str:
        return 'Output dummy'

    def shortDescription(self) -> str:
        return 'Write input frame to variable in list'

    def hasOptions(self) -> bool:
        return self.__out is not None

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return (self.__out,)

    def getEditor(self) -> AbsOperationEditor:
        pass

    def setOptions(self, outList: List[data.Frame]) -> None:
        self.__out = outList


class DummyOp(GraphOperation):
    def execute(self, df: data.Frame) -> data.Frame:
        return df

    def name(self) -> str:
        return 'Dummy operation (no-op)'

    def shortDescription(self) -> str:
        return 'This operation does nothing and returns the input dataframe'

    def setOptions(self, *args) -> None:
        pass

    def getOptions(self) -> Any:
        pass

    def hasOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        pass

    def unsetOptions(self) -> None:
        return

    def needsOptions(self) -> bool:
        return False

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

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
