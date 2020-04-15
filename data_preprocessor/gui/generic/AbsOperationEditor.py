import abc
from typing import List, Any

from PySide2.QtCore import Signal, QModelIndex
from PySide2.QtWidgets import QWidget, QDialog


class AbsOperationEditor(QWidget):
    # Signal to emit when editing is finished
    acceptAndClose = Signal()
    rejectAndClose = Signal()

    @abc.abstractmethod
    def getOptions(self) -> Any:
        """
        Return the arguments read by the editor
        Can be any type of object as required by the Operation
        :return:
        """
        pass

    @abc.abstractmethod
    def setOptions(self, index: QModelIndex) -> None:
        """
        Set the data to be visualized in the editor.
        Useful to show an existing configuration.
        Index contains information on the Operation object which may be accessed
        :param index: pointer to the Operation in the data model
        """
        pass
