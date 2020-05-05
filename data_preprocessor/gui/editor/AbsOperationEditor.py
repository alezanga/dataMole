import abc
import uuid
from typing import Iterable

from PySide2.QtCore import Signal
from PySide2.QtGui import QCloseEvent, Qt
from PySide2.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout


class AbsOperationEditor(QWidget):
    """ Base class for operation editors. Provide editors made of a custom widget and two buttons,
    one to accept and one to close and reject changes. Pressing of one of these two buttons
    emits one of two signals:

        - acceptAndClose
        - rejectAndClose
    """
    # Signal to emit when editing is finished (must be class object)
    acceptAndClose = Signal()
    rejectAndClose = Signal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.__id: str = uuid.uuid4().hex
        butOk = QPushButton('Ok')
        butCancel = QPushButton('Cancel')
        butLayout = QHBoxLayout()
        butLayout.addWidget(butCancel, alignment=Qt.AlignLeft)
        butLayout.addWidget(butOk, alignment=Qt.AlignRight)

        self._custom_widget = self.editorBody()
        layout = QVBoxLayout()
        layout.addWidget(self._custom_widget)
        layout.addLayout(butLayout)
        self.setLayout(layout)
        self.setFocusPolicy(Qt.StrongFocus)

        butOk.pressed.connect(self.acceptAndClose)
        butCancel.pressed.connect(self.rejectAndClose)

    @property
    def id(self) -> str:
        """
        The random unique identifier of the editor

        :return: the identifier as string
        """
        return self.__id

    @abc.abstractmethod
    def editorBody(self) -> QWidget:
        """
        Hook method to add widget components. This may include Qt components of every kind, as long as
        they can belong to a QWidget. This method may add fields to the instance but must return the
        widget that should be shown in the editor. This method is called from the constructor,
        so it should initialise every field which is required in getOptions and setOptions
        """
        pass

    @abc.abstractmethod
    def getOptions(self) -> Iterable:
        """
        Return the arguments read by the editor.
        Must be an iterable and parameters are passed in the same order. If
        no options are set return a list with None values

        :return: the options currently set by the user in the editor
        """
        pass

    @abc.abstractmethod
    def setOptions(self, *args, **kwargs) -> None:
        """
        Set the data to be visualized in the editor.
        Useful to show an existing configuration.

        :param args: any positional argument
        :param kwargs: any keyword argument
        """
        pass

    def closeEvent(self, event: QCloseEvent) -> None:
        """"""
        # Reject changes and close editor if the close button is pressed
        self.rejectAndClose.emit()
