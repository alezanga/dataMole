import logging
import sys
import traceback
from typing import Union

from PySide2.QtCore import QRunnable, Slot, QObject, Signal

from data_preprocessor import data
from data_preprocessor.flow import OperationNode
from data_preprocessor.operation.interface import Operation


class Worker(QRunnable):
    """
    Build a runnable object to execute an operation in a new thread
    """

    def __init__(self, executable: Union[Operation, OperationNode], *args):
        """
        Builds a worker to run an operation

        :param executable: an object with an 'execute' function which returns a data.Frame
        :param args: arguments to pass to 'execute' function (omit them if there are none)
        """
        super().__init__()
        self._executable = executable
        self._args = args
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        """ Reimplements QRunnable method to run the executable """
        try:
            result = self._executable.execute(*self._args)
        except:
            trace: str = traceback.format_exc()
            logging.error(trace)
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, trace))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class WorkerSignals(QObject):
    """
    Wraps Worker signals used to communicate with other Qt widgets.

    - finished: signal emitted when no the worker is closed
    - error(tuple): emitted when worker caught an exception. It includes 3 values: the exception
    type, the exception object and the stacktrace as string
    - result(Frame): emitted when the worker exited successfully and carries the result of the
    computation
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(data.Frame)
