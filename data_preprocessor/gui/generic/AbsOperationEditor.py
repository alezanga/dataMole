import abc
import uuid
from typing import Iterable

from PySide2.QtCore import Signal
from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import QWidget


class AbsOperationEditor(QWidget):
    # Signal to emit when editing is finished (must be class object)
    acceptAndClose = Signal()
    rejectAndClose = Signal()

    @abc.abstractmethod
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.__id: str = uuid.uuid4().hex

    @property
    def id(self) -> str:
        """
        The random unique identifier of the editor

        :return: the identifier as string
        """
        return self.__id

    @abc.abstractmethod
    def getOptions(self) -> Iterable:
        """
        Return the arguments read by the editor.
        Must be an iterable and parameters are passed in the same order

        :return: the options currently set by the user in the editor
        """
        pass

    @abc.abstractmethod
    def setOptions(self, *args, **kwargs) -> None:
        """
        Set the data to be visualized in the editor.
        Useful to show an existing configuration.
        Index contains information on the Operation object which may be accessed

        :param args: any positional argument
        :param kwargs: any keyword argument
        """
        pass

    def closeEvent(self, event: QCloseEvent) -> None:
        """"""
        # Reject changes and close editor if the close button is pressed
        self.rejectAndClose.emit()
