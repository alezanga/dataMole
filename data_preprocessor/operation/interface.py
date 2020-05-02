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
        """
        Build an operation as a command

        :param shape: the input shape of the frame given in input
        """
        # Holds the shape of the working frame
        self._shape: List[Optional[data.Shape]] = [None] * self.maxInputNumber()
        # Will hold the result when computation is done
        # self._result: data.Frame = None

    # def result(self) -> data.Frame:
    #     return self._result

    def compute(self, *input_df: data.Frame) -> data.Frame:
        """
        Private method used to run every operation. Should not be redefined.
        """
        # Check if input is set
        if self.maxInputNumber() < len(input_df) < self.minInputNumber():
            raise ValueError(
                '{}.compute(input=...), input argument not correctly set'.format(
                    self.__class__.__name__))

        # Check if options are set and correct
        msg: Optional[str] = self.checkOptions()
        if msg:
            raise ValueError('{}.compute(input=...), options check failed with message: {}'.format(
                self.__class__.__name__, msg))

        return self.execute(*input_df)

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
        :param pos: an integer index being the position to add the shape at. A negative number means
            that position does not matter
        """
        if pos >= 0:
            self._shape[pos] = shape
        else:
            raise ValueError('Argument \'pos\' must be a non negative integer')

    def removeInputShape(self, pos: int) -> None:
        """ Remove the input shape at given position, replacing it with None """
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
        Called when graph is modified and input shape(s) are removed. After this steps this function
        is called. Should be overridden to unset every option that depends on the input shape(s).
        If no options depend on the input shape it should do nothing.
        """
        pass

    @abstractmethod
    def needsOptions(self) -> bool:
        """
        Returns whether the operation needs to be configured with an editor. If this method
        returns False, then the following methods will be ignored (but must be redefined all the same):

            - :func:`~data_preprocessor.operation.Operation.getEditor`
            - :func:`~data_preprocessor.operation.Operation.getOptions`
            - :func:`~data_preprocessor.operation.Operation.setOptions`

        :return a boolean value, True if the operation needs to be configured, False otherwise
        """
        pass

    @abstractmethod
    def getOptions(self) -> Any:
        """
        Called to get current options for the operation. Typically called to get the
        existing configuration when an editor is opended

        :return: the configuration object
        """
        pass

    @abstractmethod
    def getEditor(self) -> AbsOperationEditor:
        """
        Return the editor panel to configure the step

        :return: The widget editor
        """
        pass

    @abstractmethod
    def getOutputShape(self) -> Union[data.Shape, None]:
        """
        Computes what will the frame shape be after execution of the step.
        Be careful with references. This function should not be modify the input shape.
        If the shape cannot be predicted (for every column) it must return
        None. Additionally 'isOutputShapeKnown' should be overridden accordingly. See
        :func:`~data_preprocessor.operation.Operation.isOutputShapeKnown`
        """
        pass

    @staticmethod
    @abstractmethod
    def isOutputShapeKnown() -> bool:
        """
        Must return true iff the number of columns and their types can be inferred with
        'getOutputShape'. Thus if this function returns false
        :func:`~data_preprocessor.operation.Operation.getOutputShape` must always return None
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
        This function is called before executing the operation in order to provide a method to
        check option set. Default implementation does nothing and returns None, i.e. options are ok.
        If anything else than None is returned, the 'compute' function will raise an exception showing
        the object returned (which should be an informative message).

        :return: None if computation can continue, or an error message to raise an exception. Defaults
            to None
        """
        return None


class InputOperation(Operation):
    """
    Base class for operations to be used to provide input
    These operations must not change the shape
    """

    def __init__(self, w: Workbench = None):
        super().__init__()
        self._workbench = w

    @abstractmethod
    def inferInputShape(self) -> None:
        """ This method must be reimplemented to set the input shape after the options have been set """
        pass

    def addInputShape(self, shape: data.Shape, pos: int) -> None:
        # This method should do nothing for input operations
        pass

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def getOutputShape(self) -> Union[data.Shape, None]:
        return self._shape[0]

    def unsetOptions(self) -> None:
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


class OutputOperation(Operation):
    """
    Base class for operations that persist the output of a pipeline.
    These operations must not change the shape
    """

    def __init__(self):
        super().__init__()
        self._workbench = None

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def getOutputShape(self) -> Union[data.Shape, None]:
        return self._shape[0]

    def unsetOptions(self) -> None:
        pass

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
        return 0

    @staticmethod
    def maxOutputNumber() -> int:
        return 0
