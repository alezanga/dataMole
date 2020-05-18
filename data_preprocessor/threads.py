import logging
import sys
import traceback
from typing import Tuple, Any, Union

from PySide2.QtCore import QRunnable, Slot, QObject, Signal

from data_preprocessor.flow import OperationNode
from data_preprocessor.operation.interface import SimpleOperation


class Worker(QRunnable):
    """
    Build a runnable object to execute an operation in a new thread
    """

    class WorkerSignals(QObject):
        """
        Wraps Worker signals used to communicate with other Qt widgets.

        - finished(id): signal emitted when no the worker is closed
        - error(id, tuple): emitted when worker caught an exception. It includes 3 values: the exception
        type, the exception object and the stacktrace as string
        - result(id, Frame): emitted when the worker exited successfully and carries the result of the
        computation
        """
        finished = Signal(object)
        error = Signal(object, tuple)
        result = Signal(object, object)

    def __init__(self, executable: Union[SimpleOperation, OperationNode], args: Tuple = tuple(),
                 identifier: Any = None):
        """
        Builds a worker to run an operation

        :param executable: an object with an 'execute' function which returns a data.Frame
        :param args: arguments to pass to 'execute' function (omit them if there are none)
        :param identifier: object to emit as first argument of every signal
        """
        super().__init__()
        self._executable = executable
        self._args = args
        self._identifier = identifier
        self.signals = Worker.WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        """ Reimplements QRunnable method to run the executable """
        try:
            result = self._executable.execute(*self._args)
        except:
            trace: str = traceback.format_exc()
            logging.error(trace)
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit(self._identifier, (exctype, value, trace))
        else:
            logging.debug('Worker finished with result')
            self.signals.result.emit(self._identifier, result)
        finally:
            self.signals.finished.emit(self._identifier)
