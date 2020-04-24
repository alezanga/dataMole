from typing import Any

from data_preprocessor.data import Frame
from data_preprocessor.operation import Operation


class OperationNode:
    def __init__(self, operation: Operation):
        import data_preprocessor.flow as flow
        self.uid: flow.OperationUid = flow.OperationUidFactory().getUniqueId()
        self.operation = operation
        self.__inputs = tuple()

    def __hash__(self):
        return self.uid.uid

    def __eq__(self, other):
        return other and self.uid == other.uid

    def __ne__(self, other):
        return not self.__eq__(other)

    def addInputArgument(self, arg: Any) -> None:
        self.__inputs = self.__inputs + tuple([arg])

    def compute(self) -> Frame:
        return self.operation.compute(*self.__inputs)
