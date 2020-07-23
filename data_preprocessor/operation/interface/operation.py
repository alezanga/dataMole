from abc import abstractmethod, ABC
from typing import Any, Iterable, List

from data_preprocessor.data.types import ALL_TYPES, Type


class Operation(ABC):
    """ Base class of every operation. Allows to set up a command giving arguments and executing it
    over a data.Frame """

    def __init__(self, w: 'WorkbenchModel' = None):
        super().__init__()
        self._workbench = w

    @property
    def workbench(self) -> 'WorkbenchModel':
        return self._workbench

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """ Contains the logic of the operations

        :return the result (any type)
        """
        pass

    def getOptions(self) -> Iterable:
        """
        Called to get current options set for the operation. Typically called to get the
        existing configuration when an editor is opened

        :return: a list or tuple containing all the objects needed by the editor, which will be passed
            in the same order. By default returns an empty tuple
        """
        return tuple()

    @abstractmethod
    def setOptions(self, *args, **kwargs) -> None:
        """
        Called to configure a step with the required data. If necessary it may validate the passed
        options. In order to comunicate a specific error to a widget it should use
        :class:`~data_preprocessor.operation.interface.exceptions.OptionValidationError`

        :raise OperationError: if options are not valid
        """
        pass

    @staticmethod
    def name() -> str:
        """
        The name of the step
        """
        pass

    @staticmethod
    def shortDescription() -> str:
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

    def needsOptions(self) -> bool:
        """
        Returns whether the operation needs to be configured with options.

        :return a boolean value, True if the operation needs to be configured, False otherwise
        """
        pass

    def acceptedTypes(self) -> List[Type]:
        """
        Return the column types that this operation accepts. If not relevant may avoid
        reimplementation.

        :return The list of types the operation can handle. Defaults to all types.
        """
        return ALL_TYPES

    def getEditor(self) -> 'AbsOperationEditor':
        """
        Return the editor panel to configure the step

        :return: the widget to be used as editor
        """
        pass

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        """
        Inject in the options editor every relevant field, like input shapes, accepted types and
        configure the editor components if necessary
        """
        pass
