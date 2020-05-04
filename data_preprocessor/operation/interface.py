from abc import ABC, abstractmethod
from typing import Union, Any, List, Optional

from data_preprocessor import data
from data_preprocessor.data.Workbench import Workbench
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor


class Operation(ABC):
    """
    Base interface of every operation
    """

    @abstractmethod
    def __init__(self):
        """ Initialises an operation """
        # Holds the input shapes
        self._shape: List[Optional[data.Shape]] = [None] * self.maxInputNumber()

    @abstractmethod
    def execute(self, *df: data.Frame) -> data.Frame:
        """
        Contains the logic for executing the operation.
        Must not modify the input dataframe (i.e. no in-place operations), but must modify a copy of
        it. Returning the input dataframe is allowed if the operation does nothing.

        :param df: input dataframe
        :return: the new dataframe modified as specified by the operation
        """
        pass

    @staticmethod
    @abstractmethod
    def name() -> str:
        """
        The name of the step
        """
        pass

    @abstractmethod
    def info(self) -> str:
        """
        Provide some information to show for a step
        """
        pass

    @abstractmethod
    def acceptedTypes(self) -> List[Types]:
        """ Return the column types that this operation accepts """
        pass

    def addInputShape(self, shape: data.Shape, pos: int) -> None:
        """ Setter method for the shape input

        :param shape: the shape to add
        :param pos: an integer index being the position to add the shape at. Must be non-negative and
            consistent with :func:`~data_preprocessor.operation.interface.Operation.maxInputNumber`
        :raise ValueError: if 'pos' is negative
        """
        if pos < 0:
            raise ValueError('Position must be non-negative')
        self._shape[pos] = shape

    def removeInputShape(self, pos: int) -> None:
        """ Remove the input shape at given position, replacing it with None

        :param pos: index of the shape to remove. Must be non-negative and consistent with
            :func:`~data_preprocessor.operation.interface.Operation.maxInputNumber`
        :raise ValueError: if 'pos' is negative
        """
        if pos < 0:
            raise ValueError('Position must be non-negative')
        self._shape[pos] = None

    @abstractmethod
    def setOptions(self, *args, **kwargs) -> None:
        """
        Called to configure a step with the required data.
        Typically must be called after the user set parameters in the configuration dialog
        """
        pass

    @abstractmethod
    def unsetOptions(self) -> None:
        """
        Unset every option that depends on the input shape(s). If no options depend on the input shape
            it should do nothing.

        Some context: this method is called after some input shapes are removed from an ancestor of an
        operation
        """
        pass

    @abstractmethod
    def needsOptions(self) -> bool:
        """
        Returns whether the operation needs to be configured with options. If this method
        returns False, then the following methods will be ignored (but must be redefined all the same):

            - :func:`~data_preprocessor.operation.interface.Operation.getEditor`
            - :func:`~data_preprocessor.operation.interface.Operation.getOptions`
            - :func:`~data_preprocessor.operation.interface.Operation.setOptions`

        :return a boolean value, True if the operation needs to be configured, False otherwise
        """
        pass

    @abstractmethod
    def getOptions(self) -> Any:
        """
        Called to get current options set for the operation. Typically called to get the
        existing configuration when an editor is opended

        :return: the configuration object, including everything needed by the editor
        """
        pass

    @abstractmethod
    def getEditor(self) -> AbsOperationEditor:
        """
        Return the editor panel to configure the step

        :return: the widget to be used as editor
        """
        pass

    @abstractmethod
    def getOutputShape(self) -> Union[data.Shape, None]:
        """
        Computes what will the frame shape be after execution of the step.
        Be careful with references. This function should not be modify the input shape.
        If the shape cannot be predicted (for every column) it must return
        None. Additionally 'isOutputShapeKnown' should be overridden accordingly.
        See :func:`~data_preprocessor.operation.interface.Operation.isOutputShapeKnown`
        """
        pass

    @staticmethod
    @abstractmethod
    def isOutputShapeKnown() -> bool:
        """
        Must return true iff the number of columns and their types can be inferred with
        'getOutputShape'. Thus if this function returns false, then
        :func:`~data_preprocessor.operation.interface.Operation.getOutputShape` must always return None
        """
        pass

    @staticmethod
    @abstractmethod
    def minInputNumber() -> int:
        """ Yields the minimum number of inputs required by the operation

        :return: a non-negative integer
        """
        pass

    @staticmethod
    @abstractmethod
    def maxInputNumber() -> int:
        """ Yields the maximum number of inputs the operation can accept.
            Use -1 to indicate an infinite number

        :return: a non-negative integer >= to minInputNumber or -1
        """
        pass

    @staticmethod
    @abstractmethod
    def minOutputNumber() -> int:
        """ Yields the minimum number of operations that must receive the output by the current one

        :return: a non-negative integer
        """
        pass

    @staticmethod
    @abstractmethod
    def maxOutputNumber() -> int:
        """ Yields the maximum number of outputs the operation can provide.
            Use -1 to indicate an infinite number

        :return: a non-negative integer >= to minOutputNumber or -1
        """
        pass

    def checkOptions(self) -> Optional[str]:
        """
        This function is an optional hook that may be redefined to add some checks on the options set
        before execution, and is only relevant when using the operation with the computational graph.
        But it may be used in any other context by manually calling it before the
        :func:`~data_preprocessor.operation.Operation.execute` method. Note that a call to this function
        should not placed inside the 'execute' method, otherwise the graph will run this function twice.
        Default implementation does nothing and returns None, i.e. options are ok.
        If anything else than None is returned, the graph handler will raise an exception
        showing the object returned (which should be an informative message).

        :return: None if computation can continue, or an error message to raise an exception. Defaults
            to None
        """
        return None


class InputOperation(Operation):
    """
    Base class for operations to be used to provide input.
    These operations have no input, an unbounded number of outputs and do not modify the input shape.
    Additionally every InputOperation has access to the workbench, in order to be able to access
    variables to use as input
    """

    def __init__(self, w: Workbench = None):
        """ Sets the workbench of the input operation

        :param w: a workbench
        """
        super().__init__()
        self._workbench: Workbench = w

    @abstractmethod
    def inferInputShape(self) -> None:
        """ This method must be reimplemented to set the input shape after the options have been set.
        If the input shape cannot be inferred it should set it to None.
        It replaces :func:`~data_preprocessor.operation.interface.InputOperation.addInputShape`,
        which instead should not be used in InputOperation
        """
        pass

    def addInputShape(self, shape: data.Shape, pos: int) -> None:
        """ It intentionally is a no-op, because input-operations has no input argument. Instead the
        input shape should be inferred using method
        :func:`~data_preprocessor.operation.interface.InputOperation.inferInputShape`
        """
        pass

    def acceptedTypes(self) -> List[Types]:
        """ Accepts all types """
        # Input operations are not concerned with types
        return ALL_TYPES

    def getOutputShape(self) -> Union[data.Shape, None]:
        """ Returns the single input shape unchanged """
        # Input operation has only one input, and it does not change input shape
        return self._shape[0]

    def unsetOptions(self) -> None:
        """ Reimplements base operation and does nothing, since no options depends on the input shape """
        pass

    @staticmethod
    def isOutputShapeKnown() -> bool:
        """ Returns True, since InputOperations are always able to know the output shape """
        return True

    @staticmethod
    def minInputNumber() -> int:
        """ Returns 0 """
        return 0

    @staticmethod
    def maxInputNumber() -> int:
        """ Returns 0 """
        return 0

    @staticmethod
    def minOutputNumber() -> int:
        """ Returns 1 """
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        """ Returns -1 """
        return -1


class OutputOperation(Operation):
    """
    Base class for operations to be used to persist output.
    These operations have exactly one input, no outputs and do not modify the input
    shape.
    Additionally every OutputOperation has access to the workbench, in order to be able write new
    variables
    """

    def __init__(self, w: Workbench = None):
        """ Sets the workbench of the output operation

        :param w: a workbench
        """
        super().__init__()
        self._workbench: Workbench = w

    def acceptedTypes(self) -> List[Types]:
        """ Accepts all types """
        return ALL_TYPES

    def getOutputShape(self) -> Union[data.Shape, None]:
        """ Returns the single input shape unchanged """
        return self._shape[0]

    def unsetOptions(self) -> None:
        """ Does nothing by default, but may be overridden if options depends on the input shape """
        pass

    @staticmethod
    def isOutputShapeKnown() -> bool:
        """ Returns True """
        return True

    @staticmethod
    def minInputNumber() -> int:
        """ Returns 1 """
        return 1

    @staticmethod
    def maxInputNumber() -> int:
        """ Returns 1 """
        return 1

    @staticmethod
    def minOutputNumber() -> int:
        """ Returns 0 """
        return 0

    @staticmethod
    def maxOutputNumber() -> int:
        """ Returns 0 """
        return 0
