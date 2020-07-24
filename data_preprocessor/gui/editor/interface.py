import abc
from typing import Iterable, List, Optional, Dict, Callable, Tuple

from PySide2.QtCore import Signal, Slot, QSize
from PySide2.QtGui import QCloseEvent, Qt, QCursor, QKeyEvent
from PySide2.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QWhatsThis, \
    QSizePolicy

from data_preprocessor import data
from data_preprocessor.data.types import Type


class AbsOperationEditor(QWidget):
    """ Base class for operation editors. Provide editors made of a custom widget and two buttons,
    one to accept and one to close and reject changes. Pressing of one of these two buttons
    emits one of two signals:

        - accept
        - reject
    """
    # Signal to emit when editing is finished (must be class object)
    accept = Signal()
    reject = Signal()

    # ----------------------------------------------------------------------------
    # ---------------------- FINAL METHODS (PLS NO OVERRIDE) ---------------------
    # ----------------------------------------------------------------------------

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # Standard options
        self.errorHandlers: Dict[str, Callable] = dict()
        self.acceptedTypes: List[Type] = list()
        self.inputShapes: List[Optional[data.Shape]] = list()
        self.workbench: 'WorkbenchModel' = None

        # Set up buttons
        self._butOk = QPushButton('Ok')
        butCancel = QPushButton('Cancel')
        self.butLayout = QHBoxLayout()
        self.butLayout.addWidget(butCancel, alignment=Qt.AlignLeft)
        self.butLayout.addWidget(self._butOk, alignment=Qt.AlignRight)

        self.__helpVerticalLayout = QVBoxLayout()
        self.__helpLayout = QHBoxLayout()
        self.__descLabel = QLabel()
        self.__helpLayout.addWidget(self.__descLabel, 7)
        self.__descLabel.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        self.__helpVerticalLayout.addLayout(self.__helpLayout)
        ll = QLabel('<hr>')
        ll.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.__helpVerticalLayout.addWidget(ll)

        self.errorLabel = QLabel(self)
        self.errorLabel.setWordWrap(True)
        self.errorLabel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self._layout = QVBoxLayout()
        self._layout.addLayout(self.__helpVerticalLayout, 1)
        self._layout.addWidget(self.errorLabel, 1)
        ll = QLabel('<hr>')
        ll.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._layout.addWidget(ll, 1)
        self._layout.addLayout(self.butLayout, 1)
        self.setLayout(self._layout)
        self.setFocusPolicy(Qt.StrongFocus)
        self.errorLabel.hide()
        self.setMinimumWidth(400)

        self._butOk.pressed.connect(self.onAcceptSlot)
        butCancel.pressed.connect(self.reject)  # emit reject
        self.__sh: Optional[QSize] = None  # Qt sizeHint property

    def setDescription(self, short: str, long: str) -> None:
        self.__descLabel.setText(short)
        self.__descLabel.setWordWrap(True)
        if long:
            whatsThisButton = QPushButton('More')
            whatsThisButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            self.__helpLayout.addWidget(whatsThisButton, 1)
            self.setWhatsThis(long)
            whatsThisButton.clicked.connect(
                lambda: QWhatsThis.showText(QCursor.pos(), long, self))

    def closeEvent(self, event: QCloseEvent) -> None:
        """ Reject changes and close editor if the close button is pressed """
        self.reject.emit()

    def setUpEditor(self):
        """ Calls editorBody and add the returned widget """
        w = self.editorBody()
        w.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        self._layout.insertWidget(1, w)

    def handleErrors(self, errors: List[Tuple[str, str]]) -> None:
        """ Provide a list of readable errors to be shown in the widget

        :param errors: list of (errorName, errorMessage). If 'errorName' is available in
        the widget errorHandlers field the corresponding callback will be fired with the 'errorMessage'
        This is useful to show custom error messages in specific parts of the editor widget
        """
        self.errorLabel.hide()
        text = ''
        for (field, message) in errors:
            handler = self.errorHandlers.get(field, None)
            if handler:
                handler(message)
            else:
                text += '<br>' + message
        text = text.strip('<br>')
        if text:
            # Default message on bottom
            self.errorLabel.setText(text)
            self.errorLabel.setStyleSheet('color: red;')
            self.errorLabel.show()

    def disableOkButton(self) -> None:
        """ Makes the accept button uncheckable.
            Useful to prevent user from saving invalid changes """
        self._butOk.setDisabled(True)

    def enableOkButton(self) -> None:
        """ Enable the accept button """
        self._butOk.setEnabled(True)

    @Slot()
    def onAcceptSlot(self) -> None:
        self.onAccept()
        self.accept.emit()

    def setSizeHint(self, w: int, h: int) -> None:
        """ Set the editor sizeHint property.
         This function is provided for convenience: it is equivalent to reimplementing sizeHint()
         directly in a subclass.
        """
        self.__sh = QSize(w, h)

    def sizeHint(self) -> QSize:
        if self.__sh:
            return self.__sh
        return super().sizeHint()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.reject.emit()
        else:
            super().keyPressEvent(event)

    # ----------------------------------------------------------------------------
    # ------------------------------ VIRTUAL METHODS -----------------------------
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

    def setOptions(self, *args, **kwargs) -> None:
        """
        Set the data to be visualized in the editor.
        Useful to show an existing configuration. Does nothing by default

        :param args: any positional argument.
        """
        pass

    def onAccept(self) -> None:
        """
        Method called when the user accepts current options (e.g. clicks the Ok button),
        immediately before emitting the 'accept' signal. Useful to do additional actions over
        options before setting them in the operation. Does nothing by default
        """
        pass
