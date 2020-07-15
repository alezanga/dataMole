from typing import List, Tuple


class GException(Exception):
    """ Superclass of all exceptions """

    def __init__(self, title: str = '', message: str = ''):
        super().__init__()
        self.title: str = title
        self.message: str = message

    def __str__(self) -> str:
        return self.message


# Dag handler

class HandlerException(GException):
    """ Used to signal exceptional condition in the dag handler """
    pass


class DagException(GException):
    """ Signal error during graph update/manipulation """
    pass


# Operations

class OperationError(GException):
    """ Base class for operation exceptions """

    def __init__(self, message: str):
        super().__init__(title=self.__class__.__name__, message=message)


class OptionValidationError(OperationError):
    """ Used to signal specific errors in the Operation options """

    def __init__(self, invalid: List[Tuple[str, str]], message=None):
        """

        :param invalid: for each error contains a tuple with the error name and its message. To show
        errors in an AbsOperationEditor error name must be between the defined errorHandlers
        :param message: this field is ignored by all AbsOperationEditor
        """
        super().__init__(message)
        self.invalid: List[Tuple[str, str]] = invalid


class InvalidOptions(OperationError):
    """ Signal a generic error in options. To link an error message to a specific option use
    OptionValidationError """
    pass
