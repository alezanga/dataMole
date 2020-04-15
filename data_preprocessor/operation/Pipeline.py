from typing import List

from data_preprocessor.data import Frame
from data_preprocessor.operation import Operation


class Pipeline:
    def __init__(self, id_df: int, ops: List[Operation] = None):
        self._operations: List[Operation] = ops if ops else list()
        self._id_df: int = id_df

    def add(self, op: Operation) -> None:
        self._operations.append(op)

    def remove(self, op_index: int) -> None:
        self._operations.pop(op_index)

    def execute(self) -> Frame:
        f = Frame()
        for op in self._operations:
            f = op.execute(f)
        return f

