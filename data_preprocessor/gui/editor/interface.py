import abc
import uuid
from typing import Iterable, List, Optional

from PySide2.QtCore import Signal, Slot
from PySide2.QtGui import QCloseEvent, Qt
from PySide2.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui.waitingspinnerwidget import QtWaitingSpinner


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

    # ----------------------------------------------------------------------------
    # ---------------------- FINAL METHODS (PLS NO OVERRIDE) ---------------------
    # ----------------------------------------------------------------------------

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # Call hook method
        # self._custom_widget = self.editorBody()

        # Standard options
        self._acceptedTypes: List[Types] = list()
        self._inputShapes: List[Optional[data.Shape]] = list()
        self._workbench: 'WorkbenchModel' = None

        # Set up buttons
        self.__id: str = uuid.uuid4().hex
        self.__butOk = QPushButton('Ok')
        butCancel = QPushButton('Cancel')
        self.butLayout = QHBoxLayout()
        self.butLayout.addWidget(butCancel, alignment=Qt.AlignLeft)
        self.butLayout.addWidget(self.__butOk, alignment=Qt.AlignRight)

        layout = QVBoxLayout()
        # layout.addWidget(self._custom_widget)
        layout.addLayout(self.butLayout)
        self.setLayout(layout)
        self.setFocusPolicy(Qt.StrongFocus)

        self.__butOk.pressed.connect(self.onAccept)
        butCancel.pressed.connect(self.rejectAndClose)

    @property
    def id(self) -> str:
        """
        The random unique identifier of the editor

        :return: the identifier as string
        """
        return self.__id

    def setTypes(self, types: List[Types]) -> None:
        """ Set the accepted types in the editor """
        self._acceptedTypes: List[Types] = types

    def setInputShapes(self, sh: List[Optional[data.Shape]]) -> None:
        """ Sets the input shapes in the editor """
        self._inputShapes: List[Optional[data.Shape]] = sh

    def setWorkbench(self, wor: 'WorkbenchModel') -> None:
        self._workbench: 'WorkbenchModel' = wor

    def disableOkButton(self) -> None:
        """ Makes the accept button unclickable.
            Useful to prevent user from saving invalid changes """
        self.__butOk.setDisabled(True)

    def enableOkButton(self) -> None:
        """ Enable the accept button """
        self.__butOk.setEnabled(True)

    def closeEvent(self, event: QCloseEvent) -> None:
        """"""
        # Reject changes and close editor if the close button is pressed
        self.rejectAndClose.emit()

    # def setInputShapes(self, shapes: List[Optional[data.Shape]]) -> None:
    #     self._inputShapes = shapes

    @Slot()
    def onAccept(self) -> None:
        ok = self.validate(*self.getOptions())
        if ok:
            self.acceptAndClose.emit()

    def setUpEditor(self):
        """ Calls editorBody and add the returned widget """
        layout: QVBoxLayout = self.layout()
        layout.insertWidget(0, self.editorBody())

    # ----------------------------------------------------------------------------
    # --------------------------- PURE VIRTUAL METHODS ---------------------------
    # ----------------------------------------------------------------------------

    @abc.abstractmethod
    def editorBody(self) -> QWidget:
        """
        Hook method to add widget components. This may include Qt components of every kind, as long as
        they can belong to a QWidget. This method may add fields to the instance but must return the
        widget that should be shown in the editor. This method is called after the constructor
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

    def validate(self, *args) -> bool:
        """
        Validates the options returned by 'getOptions'. This method should be used to show error
        messages if some fields were not imputed correctly. If this method returns False, the editor
        will not be closed. The Ok button may be disabled to force the user to correct fields.
        Default implementation does nothing and returns True.

        :param args: the arguments returned by 'getOptions'
        :return: True if options are ok, False otherwise. Defaults to True
        """
        return True


def withSpinner(editor: AbsOperationEditor) -> AbsOperationEditor:
    """ Adds a spinner which can be shown next to the Ok button. Disable the editor when started """
    editor.spinner = QtWaitingSpinner(editor, centerOnParent=False, disableParentWhenSpinning=True)
    editor.butLayout.insertWidget(1, editor.spinner, alignment=Qt.AlignRight)
    editor.spinner.setInnerRadius(6)
    return editor
