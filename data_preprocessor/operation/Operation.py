from abc import ABC, abstractmethod
from typing import Union, Any, List, Optional

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui import AbsOperationEditor
# TODO: see https://realpython.com/python-interface/#using-metaclasses
from data_preprocessor.operation import OperationUid


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
        self._shape: data.Shape = None
        # Will hold the result when computation is done
        self._result: data.Frame = None
        # Keeps a unique identifier for an operation
        self.connectionObj = OperationUid()

    def result(self) -> data.Frame:
        return self._result

    def compute(self, *input_df: data.Frame) -> None:
        """
        Private method used to run every operation. Should not be redefined.
        """
        # Check if input is set
        if not input_df or self.maxInputNumber() < len(input_df) < self.minInputNumber():
            raise ValueError(
                '{}.compute(input=...), input argument not correctly set'.format(
                    self.__class__.__name__))

        # Check if options are set and correct
        msg: Optional[str] = self.checkOptions()
        if msg:
            raise ValueError('{}.compute(input=...), options check failed with message: {}'.format(
                self.__class__.__name__, msg))

        self._result = self.execute(*input_df)

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

    @abstractmethod
    def name(self) -> str:
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

    def setInputShape(self, shape: data.Shape) -> None:
        """ Setter method for the concrete input """
        self._shape = shape

    @abstractmethod
    def setOptions(self, *args, **kwargs) -> None:
        """
        Called to configure a step with the required data.
        Typically must be called after the user set parameters in the configuration dialog
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
        :func:`~data_preprocessor.operation.Operation.getOutputShape` must return None
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
