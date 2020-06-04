from abc import ABC, abstractmethod


class ExecutionLog(ABC):
    @abstractmethod
    def logMessage(self) -> str:
        """
        The formatted message to log after an operation completes. Should include details about
        the execution, like learned parameters or anything that can only be known inside the
        :func:`~data_preprocessor.operation.interface.GraphOperation.execute` method """
        pass
