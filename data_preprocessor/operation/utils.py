from typing import Optional, Iterable

from PySide2.QtCore import Slot, QObject, Signal, QPoint
from PySide2.QtWidgets import QMessageBox, QAction

from data_preprocessor import data
from data_preprocessor.gui.editor.interface import withSpinner
from data_preprocessor.operation.interface import Operation


class OperationAction(QObject):
    """
    Wraps an operation allowing it to be executed as a single command.
    'createAction' will return a QAction which, once triggered, will ask the user to provide
    options if necessary through the option editor. When the operation completes the object will emit
    a 'finished' signal. The result can then be retrieved with the 'output' property
    """
    finished = Signal()

    def __init__(self, op: Operation, parent: QObject, name: str = '',
                 editorPosition: QPoint = QPoint()):
        super().__init__(parent)

        # handler = SingleOperation(op, parent.rect().center(), parent)
        self._action = QAction(parent) if not name else QAction(name, parent)
        self.operation = op
        self.editor = None
        self._editorPos = editorPosition
        self._inputs: Iterable[data.Frame] = tuple()
        self._output: Optional[data.Frame] = None
        self._action.triggered.connect(self.start)

    @property
    def output(self) -> Optional[data.Frame]:
        return self._output

    def createAction(self, inputs: Iterable[data.Frame] = tuple()) -> QAction:
        """ Retrieve the action. When triggered this action allows to start the operation by showing
        the editor """
        self._inputs = inputs
        return self._action

    @Slot()
    def start(self):
        self.editor = withSpinner(self.operation.getEditor())
        self.editor.acceptAndClose.connect(self.onAcceptEditor)
        self.editor.rejectAndClose.connect(self.onCloseEditor)
        self.editor.setTypes(self.operation.acceptedTypes())
        self.editor.setInputShapes([i.shape for i in self._inputs])
        self.editor.setUpEditor()
        self.editor.setOptions(*self.operation.getOptions())
        self.editor.setParent(None)
        self.editor.move(self._editorPos)
        self.editor.show()

    @Slot()
    def onCloseEditor(self) -> None:
        self.editor.disconnect(self)
        self.editor.deleteLater()
        self.editor = None

    @Slot()
    def onAcceptEditor(self) -> None:
        self.editor.spinner.start()
        self.operation.setOptions(*self.editor.getOptions())
        # Execute operation
        try:
            if not self._inputs:
                output = self.operation.execute()
            elif isinstance(self._inputs, tuple):
                output = self.operation.execute(*self._inputs)
            else:
                output = self.operation.execute(self._inputs)
        except Exception as e:
            self._showError(str(e))
            self.editor.spinner.stop()
            return
        self.editor.spinner.stop()
        self._output = output
        self.finished.emit()
        self.onCloseEditor()

    def _showError(self, msg: str) -> None:
        msg_short = 'Operation failed to execute with following message: <br> {}'.format(msg[:80])
        if len(msg) > 80:
            msg_short += '... (see all in log)'
        msgbox = QMessageBox(QMessageBox.Icon.Critical, 'Critical error', msg_short, QMessageBox.Ok,
                             self.editor)
        msgbox.exec_()
