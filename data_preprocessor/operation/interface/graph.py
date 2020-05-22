from abc import abstractmethod
from typing import Union, List, Optional, Iterable

from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from data_preprocessor.gui.workbench import WorkbenchModel
from .operation import Operation


class GraphOperation(Operation):
    """
    Base interface of every graph operation
    """

    def __init__(self):
        """ Initialises an operation """
        # Holds the input shapes
        self._shape: List[Optional[data.Shape]] = [None] * self.maxInputNumber()

    # ----------------------------------------------------------------------------
    # ---------------------- FINAL METHODS (PLS NO OVERRIDE) ---------------------
    # ----------------------------------------------------------------------------

    @property
    def shapes(self) -> List[Optional[data.Shape]]:
        return self._shape

    def addInputShape(self, shape: data.Shape, pos: int) -> None:
        """ Setter method for the shape input

        :param shape: the shape to add
        :param pos: an integer index being the position to add the shape at. Must be non-negative and
            consistent with :func:`~data_preprocessor.operation.interface.GraphOperation.maxInputNumber`
        :raise ValueError: if 'pos' is negative
        """
        if pos < 0:
            raise ValueError('Position must be non-negative')
        self._shape[pos] = shape

    def removeInputShape(self, pos: int) -> None:
        """ Remove the input shape at given position, replacing it with None

        :param pos: index of the shape to remove. Must be non-negative and consistent with
            :func:`~data_preprocessor.operation.interface.GraphOperation.maxInputNumber`
        :raise ValueError: if 'pos' is negative
        """
        if pos < 0:
            raise ValueError('Position must be non-negative')
        self._shape[pos] = None

    # ---------------------------------------------------------
    # -------------------- VIRTUAL METHODS --------------------
    # ---------------------------------------------------------

    def getOutputShape(self) -> Union[data.Shape, None]:
        """
        Computes what will the frame shape be after execution of the step.
        Be careful with references. This function should not modify the input shape.
        If the shape cannot be predicted it must return
        None. This is also the case when not all options are set. By default it returns None if any
        options/input shapes are not set, and otherwise it tries to infer the output shapes by running
        the 'execute' method with dummy frames.
        Additionally 'isOutputShapeKnown' should be overridden accordingly.
        See :func:`~data_preprocessor.operation.interface.GraphOperation.isOutputShapeKnown`
        """
        # If shapes or options are not set
        if not all(self._shape) or not self.hasOptions():
            return None
            # Try to execute the operation with dummy frames
        dummy_frames = map(data.Frame.fromShape, self._shape)
        result = self.execute(*dummy_frames)
        return result.shape

    def acceptedTypes(self) -> List[Types]:
        """
        Return the column types that this operation accepts. If not relevant may avoid
        reimplementation.

        :return The list of types the operation can handle. Defaults to all types.
        """
        return ALL_TYPES

    @staticmethod
    def isOutputShapeKnown() -> bool:
        """
        Must return True if the number of columns and their types can be inferred with
        'getOutputShape'. Thus if this function returns False, then
        :func:`~data_preprocessor.operation.interface.GraphOperation.getOutputShape` must always return None

        :return True if the output shape cannot be predicted, False otherwise. Defaults to True
        """
        return True

    @staticmethod
    def needsInputShapeKnown() -> bool:
        """
        Tells if the operation needs the input shape set to be configured. If the operation has no
        options depending on the input shape, this method should return False. When this method returns
        True only operations with :func:`~data_preprocessor.operation.interface.GraphOperation
        .isOutputShapeKnown` set to True can be used as its input. Otherwise all operations can be
        used, regardless of their output shape. One should consider that the input shape is set
        regardless of the result of this method, which is only used when determining if a graph
        connection can be added.

        :return True if the operation needs the input shape, otherwise False. Defaults to True
        """
        return True

    # ----------------------------------------------------------------------------
    # --------------------------- PURE VIRTUAL METHODS ---------------------------
    # ----------------------------------------------------------------------------

    @abstractmethod
    def execute(self, *df: data.Frame) -> data.Frame:
        """
        Contains the logic for executing the operation.
        Must not modify the input dataframe (i.e. no in-place operations), but must modify a copy of
        it. Returning the input dataframe is allowed if the operation does nothing.
        If the method is called to operate on attribute types which are not accepted, it must do nothing.
        See :func:`~data_preprocessor.operation.interface.GraphOperation.acceptedTypes`

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
    def shortDescription(self) -> str:
        """
        Provide some information to show for a step. Should be short, since it is always shown in the
        editor widget

        :return a string also with html formatting
        """
        pass

    def longDescription(self) -> str:
        """
        A textual description which may be useful to configure the options. It is shown on demand
        if the user needs further information over the short description. May be long and include html
        tags

        :return: a string also with html formatting
        """
        return None

    @abstractmethod
    def hasOptions(self) -> bool:
        """
        This must be redefined to tell if all necessary options are set in the operation. These
        options include all fields that the must be supplied by the user. It must not check the input
        shape or any other variable which is not responsibility of the user to check. It is
        used by getOutputShape to verify if the shape can be inferred. It is also run before execution
        of the operation in the computational graph.
        It may be used in any other context by manually calling it before the
        :func:`~data_preprocessor.operation.GraphOperation.execute` method.
        Note that a call to this function should not placed inside the 'execute' method.

        :return: True if computation can continue, False otherwise
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

            - :func:`~data_preprocessor.operation.interface.GraphOperation.getEditor`
            - :func:`~data_preprocessor.operation.interface.GraphOperation.getOptions`
            - :func:`~data_preprocessor.operation.interface.GraphOperation.setOptions`

        :return a boolean value, True if the operation needs to be configured, False otherwise
        """
        pass

    @abstractmethod
    def getOptions(self) -> Iterable:
        """
        Called to get current options set for the operation. Typically called to get the
        existing configuration when an editor is opended

        :return: a list or tuple containing all the objects needed by the editor, which will be passed
            in the same order
        """
        pass

    @abstractmethod
    def getEditor(self) -> AbsOperationEditor:
        """
        Return the editor panel to configure the step

        :return: the widget to be used as editor
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


class InputGraphOperation(GraphOperation):
    """
    Base class for operations to be used to provide input.
    These operations have no input, an unbounded number of outputs and do not modify the input shape.
    Additionally every InputGraphOperation has access to the workbench, in order to be able to access
    variables to use as input
    """

    def __init__(self, w: WorkbenchModel = None):
        """ Sets the workbench of the input operation

        :param w: a workbench
        """
        super().__init__()
        self._workbench: WorkbenchModel = w

    @property
    def workbench(self) -> WorkbenchModel:
        return self._workbench

    # @abstractmethod
    # def inferInputShape(self) -> None:
    #     """ This method must be reimplemented to set the input shape after the options have been set.
    #     If the input shape cannot be inferred it should set it to None.
    #     It replaces :func:`~data_preprocessor.operation.interface.InputGraphOperation.addInputShape`,
    #     which instead should not be used in InputGraphOperation
    #     """
    #     pass

    def addInputShape(self, shape: data.Shape, pos: int) -> None:
        """ It intentionally is a no-op, because input-operations has no input argument. Instead the
        input shape should be inferred using method
        :func:`~data_preprocessor.operation.interface.InputGraphOperation.inferInputShape`
        """
        pass

    def acceptedTypes(self) -> List[Types]:
        """ Accepts all types """
        # Input operations are not concerned with types
        return ALL_TYPES

    @abstractmethod
    def getOutputShape(self) -> Union[data.Shape, None]:
        """ Returns the single input shape which must be inferred from options """
        pass

    def unsetOptions(self) -> None:
        """ Reimplements base operation and does nothing, since no options depends on the input shape """
        pass

    @staticmethod
    def isOutputShapeKnown() -> bool:
        """ Returns True, since InputOperations are always able to know the output shape """
        return True

    @staticmethod
    def needsInputShapeKnown() -> bool:
        """ Reimplements and does nothing, since this method doesn't apply to input operations """
        pass

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


class OutputGraphOperation(GraphOperation):
    """
    Base class for operations to be used to persist output.
    These operations have exactly one input, no outputs and do not modify the input
    shape.
    Additionally every OutputGraphOperation has access to the workbench, in order to be able write new
    variables
    """

    def __init__(self, w: WorkbenchModel = None):
        """ Sets the workbench of the output operation

        :param w: a workbench
        """
        super().__init__()
        self._workbench: WorkbenchModel = w

    @property
    def workbench(self) -> WorkbenchModel:
        return self._workbench

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
    def needsInputShapeKnown() -> bool:
        """ Reimplements to allow every operation to be connected """
        return False

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
