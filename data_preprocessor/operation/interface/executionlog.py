from abc import ABC


class OperationLog(ABC):
    def __init__(self):
        super().__init__()
        self._logString: str = None

    def logMessage(self) -> str:
        """
        Returns the formatted message to log after an operation completes. Should include details about
        the execution, like learned parameters or anything that can only be known inside the
        :func:`~data_preprocessor.operation.interface.graph.GraphOperation.execute` method. By
        default returns the parameter logString """
        return self._logString
