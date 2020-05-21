import abc
from typing import Iterable, List, Optional, Dict, Callable, Tuple

from PySide2.QtCore import Signal
from PySide2.QtGui import QCloseEvent, Qt, QCursor
from PySide2.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QWhatsThis, \
    QSizePolicy

from data_preprocessor import data
from data_preprocessor.data.types import Types


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
        self.errorHandlers: Dict[str, Callable] = dict()
        self.acceptedTypes: List[Types] = list()
        self.inputShapes: List[Optional[data.Shape]] = list()
        self.workbench: 'WorkbenchModel' = None

        # Set up buttons
        self.__butOk = QPushButton('Ok')
        butCancel = QPushButton('Cancel')
        self.butLayout = QHBoxLayout()
        self.butLayout.addWidget(butCancel, alignment=Qt.AlignLeft)
        self.butLayout.addWidget(self.__butOk, alignment=Qt.AlignRight)

        self.__helpLayout = QHBoxLayout()
        self.__descLabel = QLabel()
        self.__helpLayout.addWidget(self.__descLabel, 7)

        self._layout = QVBoxLayout()
        # layout.addWidget(self._custom_widget)
        self._layout.addLayout(self.__helpLayout)
        self._layout.addLayout(self.butLayout)
        self.setLayout(self._layout)
        self.setFocusPolicy(Qt.StrongFocus)

        self.__butOk.pressed.connect(self.acceptAndClose)
        butCancel.pressed.connect(self.rejectAndClose)

    def setDescription(self, short: str, long: str) -> None:
        self.__descLabel.setText(short)
        self.__descLabel.setWordWrap(True)
        if long:
            whatsThisButton = QPushButton('More')
            whatsThisButton.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.__helpLayout.addWidget(whatsThisButton, 1)
            self.setWhatsThis(long)
            whatsThisButton.clicked.connect(
                lambda: QWhatsThis.showText(QCursor.pos(), long, self))

    def closeEvent(self, event: QCloseEvent) -> None:
        """"""
        # Reject changes and close editor if the close button is pressed
        self.rejectAndClose.emit()

    def setUpEditor(self):
        """ Calls editorBody and add the returned widget """
        self._layout.insertWidget(1, self.editorBody())

    def handleErrors(self, errors: List[Tuple[str, str]]) -> None:
        """ Provide a list of readable errors to be shown in the widget

        :param errors: list of (errorName, errorMessage). If 'errorName' is available in
        the widget errorHandlers field the corresponding callback will be fired with the 'errorMessage'
        This is useful to show custom error messages in specific parts of the editor widget
        """
        for (field, message) in errors:
            handler = self.errorHandlers.get(field, None)
            if handler:
                handler(message)

    def disableOkButton(self) -> None:
        """ Makes the accept button unclickable.
            Useful to prevent user from saving invalid changes """
        self.__butOk.setDisabled(True)

    def enableOkButton(self) -> None:
        """ Enable the accept button """
        self.__butOk.setEnabled(True)

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
