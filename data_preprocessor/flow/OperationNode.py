from typing import Any, Dict, List

from data_preprocessor.data import Frame, Shape
from data_preprocessor.operation import Operation
from .OperationUid import OperationUid, OperationUidFactory


class OperationNode:
    """ Wraps an operation """

    def __init__(self, operation: Operation):
        # import data_preprocessor.flow as flow
        self._uid: OperationUid = OperationUidFactory().getUniqueId()
        self.operation = operation
        # List of inputs, kept in order
        self.__inputs: List = [None] * operation.maxInputNumber()
        # map { operation_id: position }
        self.__input_order: Dict[int, int] = dict()

    @property
    def uid(self) -> int:
        return self._uid.uid

    def __hash__(self) -> int:
        return self._uid.uid

    def __eq__(self, other):
        return other and self.uid == other.uid

    def __ne__(self, other):
        return not self.__eq__(other)

    def setSourceOperationInputPosition(self, op_id: int, pos: int) -> None:
        """ Call this method to ensure that the output of one parent (source) operation is always passed
        at a specified position when the execute method is called

        :param op_id: the unique id of the operation
        :param pos: the position, which means that input is passed as the argument at position 'pos'
        to 'execute' method. Must be non-negative
        """
        self.__input_order[op_id] = pos

    def unsetSourceOperationInputPosition(self, op_id: int) -> None:
        """ Delete the entry for specified operation in the input mapper """
        del self.__input_order[op_id]

    def addInputArgument(self, arg: Any, op_id: int) -> None:
        """ Add the input argument of an operation to the existing inputs

        :param arg: the input to add
        :param op_id: the unique id of the operation which generated the input. Defaults to None. If the
        operation only has 1 input or the order of the inputs does not matter you can avoid to pass this
        parameter
        """
        if op_id is None:
            raise ValueError('Missing argument op_id')

        pos = self.__input_order.get(op_id, None)
        self.__inputs[pos] = arg

    def addInputShape(self, shape: Shape, op_id: int) -> None:
        """ Adds the input shape coming from operation with specified id

        :param shape: the shape
        :param op_id: the id of the operation which generated the shape
        """
        if op_id is None:
            raise ValueError('Missing argument op_id')
        pos = self.__input_order.get(op_id, None)
        self.operation.addInputShape(shape, pos)

    def removeInputShape(self, op_id: int) -> None:
        pos = self.__input_order.get(op_id)
        self.operation.removeInputShape(pos)

    def clearInputArgument(self) -> None:
        """ Delete inputs """
        del self.__inputs

    def compute(self) -> Frame:
        """ Execute the operation with input arguments """
        return self.operation.compute(*[i for i in self.__inputs if i is not None])
