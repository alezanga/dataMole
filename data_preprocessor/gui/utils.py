import logging
from typing import Optional, Tuple

from PySide2.QtCore import Slot, QObject, Signal, QPoint
from PySide2.QtWidgets import QMessageBox, QAction, QWidget, QMainWindow, QApplication

from data_preprocessor import data
from data_preprocessor import threads
from data_preprocessor.operation.interface.graph import GraphOperation


class OperationAction(QObject):
    """
    Wraps an operation allowing it to be executed as a single command.
    'createAction' will return a QAction which, once triggered, will ask the user to provide
    options if necessary through the option editor. When the operation completes the object will emit
    a 'finished' signal. The result can then be retrieved with the 'output' property
    """
    success = Signal()

    def __init__(self, op: GraphOperation, parent: QObject, name: str = '',
                 editorPosition: QPoint = QPoint()):
        super().__init__(parent)

        # handler = SingleOperation(op, parent.rect().center(), parent)
        self._action = QAction(parent) if not name else QAction(name, parent)
        self.operation = op
        self.editor: Optional[QWidget] = None
        self._editorPos = editorPosition
        self._inputs: Tuple[data.Frame] = tuple()
        self._output: Optional[data.Frame] = None
        self._action.triggered.connect(self.start)

    @property
    def output(self) -> Optional[data.Frame]:
        """ Returns the output of the operation if completed, otherwise None. Output is consumed,
        which means that it is deleted after the first retrieval """
        a = self._output
        self._output = None
        return a

    def createAction(self, inputs: Tuple[data.Frame] = tuple()) -> QAction:
        """ Retrieve the action. When triggered this action allows to start the operation by showing
        the editor """
        self._inputs: Tuple[data.Frame] = inputs
        return self._action

    @Slot()
    def start(self):
        self.editor = self.operation.getEditor()
        self.editor.acceptAndClose.connect(self.onAcceptEditor)
        self.editor.rejectAndClose.connect(self.destroyEditor)
        self.editor.acceptedTypes = self.operation.acceptedTypes()
        self.editor.inputShapes = [i.shape for i in self._inputs]
        self.editor.setUpEditor()
        self.editor.setOptions(*self.operation.getOptions())
        self.editor.setParent(None)
        self.editor.move(self._editorPos)
        self.editor.show()

    @Slot()
    def destroyEditor(self) -> None:
        self.editor.deleteLater()
        self.editor = None

    @Slot()
    def onAcceptEditor(self) -> None:
        mainWindow = getMainWindow()
        mainWindow.statusBar().startSpinner()
        mainWindow.statusBar().showMessage('Executing operation...')
        self.operation.setOptions(*self.editor.getOptions())
        # Prepare worker
        worker = threads.Worker(self.operation, args=self._inputs)
        # Connect
        worker.signals.result.connect(self._setOutput)
        worker.signals.error.connect(self._showError)
        worker.signals.finished.connect(self._finished)
        # Start worker
        mainWindow.threadPool.start(worker)
        self.editor.hide()

    @Slot(object, object)
    def _setOutput(self, _, f: data.Frame) -> None:
        self._output = f
        self.destroyEditor()
        # Signal that result has been set
        self.success.emit()
        logging.info('GraphOperation result saved')

    @Slot(object)
    def _finished(self, _) -> None:
        logging.info('GraphOperation {} finished'.format(self.operation.name()))
        getMainWindow().statusBar().stopSpinner()
        getMainWindow().statusBar().showMessage('GraphOperation finished')

    @Slot(object, tuple)
    def _showError(self, _, error: Tuple[type, Exception, str]) -> None:
        msg = str(error[1])
        msg_short = 'GraphOperation failed to execute with following message: <br> {}'.format(msg[:80])
        if len(msg) > 80:
            msg_short += '... (see all in log)'
        msgbox = QMessageBox(QMessageBox.Icon.Critical, 'Critical error', msg_short, QMessageBox.Ok,
                             self.editor)
        logging.critical('GraphOperation {} failed with exception {}: {} - trace: {}'.format(
            self.operation.name(), str(error[0]), msg, error[2]))
        self.editor.show()
        msgbox.exec_()


def getMainWindow() -> Optional[QMainWindow]:
    """ Returns the application main window if it exists """
    for w in QApplication.topLevelWidgets():
        if isinstance(w, QMainWindow):
            return w
    return None
