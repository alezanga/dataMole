from typing import Any, Dict, List, Optional

from data_preprocessor.data import Frame, Shape
from data_preprocessor.operation.interface import Operation
from .OperationUid import OperationUid, OperationUidFactory


class OperationNode:
    """ Wraps an operation, providing functionality required for graph computation """

    def __init__(self, operation: Operation):
        self.__op_uid: OperationUid = OperationUidFactory().getUniqueId()
        self.operation = operation
        # List of inputs, kept in order
        self.__inputs: List = [None] * operation.maxInputNumber()
        # Input mapper { operation_id: position }
        self.__input_order: Dict[int, int] = dict()

    @property
    def uid(self) -> int:
        """ Returns the integer unique identifier of one node """
        return self.__op_uid.uid

    def inputShapeFrom(self, node_id: int) -> Optional[Shape]:
        """ Get the input shape set from specified source node, if set """
        return self.operation._shape[self.__input_order[node_id]]

    @property
    def nInputs(self) -> int:
        inputs = [i for i in self.__inputs if i is not None]
        return len(inputs)

    def setSourceOperationInputPosition(self, op_id: int, pos: int) -> None:
        """ Call this method to ensure that the output of one parent (source) operation is always passed
        at a specified position when the execute method is called

        :param op_id: the unique id of the operation
        :param pos: the position, which means that input is passed as the argument at position 'pos'
        to 'execute' method. Must be non-negative
        :raise ValueError: if 'pos' is negative
        """
        if pos < 0:
            raise ValueError('Position argument \'pos\' must be non-negative')
        self.__input_order[op_id] = pos

    def unsetSourceOperationInputPosition(self, op_id: int) -> None:
        """ Delete the entry for specified operation in the input mapper

        :param op_id: the unique id of the operation
        """
        del self.__input_order[op_id]

    def addInputArgument(self, arg: Any, op_id: int) -> None:
        """ Add the input argument of an operation to the existing inputs

        :param arg: the input to add
        :param op_id: the unique id of the operation which generated the input. This argument is
            always required
        """
        pos = self.__input_order.get(op_id, None)
        self.__inputs[pos] = arg

    def addInputShape(self, shape: Shape, op_id: int) -> None:
        """ Adds the input shape coming from operation with specified id

        :param shape: the shape
        :param op_id: the id of the operation which generated the shape
        """
        pos = self.__input_order.get(op_id, None)
        self.operation.addInputShape(shape, pos)

    def removeInputShape(self, op_id: int) -> None:
        """ Remove the input shape coming from specified operation

        :param op_id: the unique identifier of the operation whose input shape should be removed
        """
        pos = self.__input_order.get(op_id)
        self.operation.removeInputShape(pos)

    def clearInputArgument(self) -> None:
        """ Delete all input arguments cached in a node """
        self.__inputs: List = [None] * self.operation.maxInputNumber()

    def execute(self) -> Frame:
        """ Execute the operation with input arguments. Additionally checks that everything is
        correctly set """

        op = self.operation
        inputs = [i for i in self.__inputs if i is not None]

        # Check if input is set
        if op.maxInputNumber() < len(inputs) < op.minInputNumber():
            raise ValueError(
                '{}.execute(input=...), input argument not correctly set'.format(
                    self.__class__.__name__))

        # Check if options are set
        msg: bool = op.hasOptions()
        if not msg:
            raise ValueError('{}.execute(input=...), options check failed with message: {}'.format(
                self.__class__.__name__, msg))

        return op.execute(*inputs)
