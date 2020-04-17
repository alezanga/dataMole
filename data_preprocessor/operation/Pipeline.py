from typing import List

from data_preprocessor.data import Frame
from data_preprocessor.operation import Operation


class Pipeline:
    def __init__(self, df: Frame, ops: List[Operation] = None):
        self._operations: List[Operation] = ops if ops else list()
        # Reference to dataframe to write on
        self._df: Frame = df

    def __getitem__(self, key) -> Operation:
        return self._operations[key]

    def __setitem__(self, key, value) -> None:
        self._operations[key] = value

    def __delitem__(self, key) -> None:
        del self._operations[key]

    def __len__(self) -> int:
        return len(self._operations)

    def add(self, op: Operation) -> None:
        self._operations.append(op)

    def pop(self, op_index: int) -> Operation:
        return self._operations.pop(op_index)

    def execute(self) -> Frame:
        f = Frame()
        for op in self._operations:
            f = op.execute(f)
        return f

