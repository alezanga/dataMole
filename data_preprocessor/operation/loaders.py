from typing import Iterable, Union

import pandas as pd
from PySide2.QtCore import QObject, Slot, Signal

from data_preprocessor import data
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.operation.interface import InputOperation, Operation, InvalidOption
from ..gui.editor.loaders import LoadCSVEditor


class CsvLoader(InputOperation):
    def __init__(self, w):
        super().__init__(w)
        self.__file: str = None
        self.__separator: str = None

    def hasOptions(self) -> bool:
        return self.__file is not None and self.__separator is not None

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions():
            return None
        else:
            return self.execute().shape

    def execute(self) -> data.Frame:
        if not self.hasOptions():
            raise InvalidOption('Options are not set')
        pd_df = pd.read_csv(self.__file, sep=self.__separator)
        return data.Frame(pd_df)

    @staticmethod
    def name() -> str:
        return 'Load CSV'

    def info(self) -> str:
        return 'This command loads a dataframe from a CSV'

    def setOptions(self, file: str, separator: str) -> None:
        self.__file = file
        self.__separator = separator

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return self.__file, self.__separator

    def getEditor(self) -> AbsOperationEditor:
        return LoadCSVEditor()


class ActionWrapper(QObject):
    finished = Signal()

    def __init__(self, parent, op: Operation):
        super().__init__(parent)
        self._op = op
        self.result = None

    @Slot()
    def activateOperation(self) -> None:
        self._editor = self._op.getEditor()
        self._editor.setOptions(*self._op.getOptions())
        # Connect editor signals to slots which handle accept/reject
        self._editor.acceptAndClose.connect(self.onEditAccept)
        self._editor.rejectAndClose.connect(self.cleanupEditor)
        # Show the editor in new window
        self._editor.setParent(None)
        self._editor.show()

    @Slot()
    def onEditAccept(self) -> None:
        options = self._editor.getOptions()
        self._op.setOptions(*options)
        if self._op.maxInputNumber() == 0:
            # Input operation
            self.result = self._op.execute()
            self.finished.emit()

        self.cleanupEditor()

    @Slot()
    def cleanupEditor(self) -> None:
        # Do not call close() here, since this function is called after a closeEvent
        self._editor.disconnect(self)
        self._editor.deleteLater()
        self._editor = None
