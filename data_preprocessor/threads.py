import logging
import sys
import traceback
from typing import Union

from PySide2.QtCore import QRunnable, Slot, QObject, Signal

from data_preprocessor import data
from data_preprocessor.flow import OperationNode
from data_preprocessor.operation.interface import Operation


class Worker(QRunnable):
    def __init__(self, operation: Union[Operation, OperationNode], *args):
        super().__init__()
        self._operation = operation
        self._args = args
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            result = self._operation.execute(*self._args)
        except:
            trace: str = traceback.format_exc()
            logging.critical(trace)
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, trace))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(tuple)
    result = Signal(data.Frame)
