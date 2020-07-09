from abc import ABC
from typing import Optional


class Loggable(ABC):
    def __init__(self):
        super().__init__()
        self._logExecutionString: str = None
        self._logOptionsString: str = None

    def logOptions(self) -> Optional[str]:
        """
        Return a string which logs the options set in an operation, or None if no option are used.
        By default returns the field _logOptionsString
        """
        return self._logOptionsString

    def logMessage(self) -> Optional[str]:
        """
        Return the formatted message to log after an operation completes. Should include details about
        the execution, like learned parameters or anything that can only be known inside the
        :func:`~data_preprocessor.operation.interface.graph.GraphOperation.execute` method. By
        default returns the parameter _logExecutionString """
        return self._logExecutionString
