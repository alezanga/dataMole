import logging
import sys
import traceback

from PySide2.QtCore import QRunnable, Slot, QObject, Signal

from data_preprocessor.flow import OperationNode
from data_preprocessor.operation.interface import Operation


class NodeWorker(QRunnable):
    """
    Build a runnable object to execute an operation in a new thread
    """

    class WorkerSignals(QObject):
        """
        Wraps Worker signals used to communicate with other Qt widgets.

        - finished: signal emitted when no the worker is closed
        - error(tuple): emitted when worker caught an exception. It includes 3 values: the exception
        type, the exception object and the stacktrace as string
        - result(Frame): emitted when the worker exited successfully and carries the result of the
        computation
        """
        finished = Signal(int)
        error = Signal(int, tuple)
        result = Signal(int, object)

    def __init__(self, executable: OperationNode, *args):
        """
        Builds a worker to run an operation

        :param executable: an object with an 'execute' function which returns a data.Frame
        :param args: arguments to pass to 'execute' function (omit them if there are none)
        """
        super().__init__()
        self._executable = executable
        self._args = args
        self.signals = NodeWorker.WorkerSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self) -> None:
        """ Reimplements QRunnable method to run the executable """
        try:
            result = self._executable.execute()
        except:
            trace: str = traceback.format_exc()
            logging.error(trace)
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit(self._executable.uid, (exctype, value, trace))
        else:
            logging.debug('Worker finished with result')
            self.signals.result.emit(self._executable.uid, result)
        finally:
            self.signals.finished.emit(self._executable.uid)


class OperationWorker(QRunnable):
    """
    Build a runnable object to execute an operation in a new thread
    """

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
        result = Signal(object)

    def __init__(self, executable: Operation, *args):
        """
        Builds a worker to run an operation

        :param executable: an object with an 'execute' function which returns a data.Frame
        :param args: arguments to pass to 'execute' function (omit them if there are none)
        """
        super().__init__()
        self._executable = executable
        self._args = args
        self.signals = OperationWorker.WorkerSignals()
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
            self.signals.error.emit((exctype, value, trace))
        else:
            logging.debug('Worker finished with result')
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
