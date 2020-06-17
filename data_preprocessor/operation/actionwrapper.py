import logging
from typing import Optional, Tuple

from PySide2.QtCore import Slot, QObject, Signal, QPoint, QThreadPool
from PySide2.QtWidgets import QMessageBox, QAction

from data_preprocessor import data
from data_preprocessor import threads
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.operation import Operation


class OperationAction(QAction):
    stateChanged = Signal(str)

    def __init__(self, op: type, parent: QObject, actionName: str = '',
                 editorPosition: QPoint = QPoint(), *args, **kwargs):
        """
        Builds a QAction which can be used to run single operations on dataframes.

        :param op: the type of the operation (callable)
        :param parent: parent object of this QAction
        :param actionName: text to show as label of this QAction
        :param editorPosition: the point in which the options editor will be shown
        :param args: any arguments to pass to the operation constructor
        :param kwargs: any arguments to pass to the operation constructor
        """
        super().__init__(actionName, parent)
        self.__args = args
        self.__kwargs = kwargs
        self.__operation: type = op
        self.__editorPosition = editorPosition
        self.triggered.connect(self.startOperation)

    @Slot()
    def startOperation(self) -> None:
        w = OperationWrapper(self.__operation(*self.__args, **self.__kwargs), parent=self,
                             editorPosition=self.__editorPosition)
        w.stateChanged.connect(self.onStateChanged)
        w.start()

    @Slot(str)
    def onStateChanged(self, state: str):
        if state == 'finish':
            sender: OperationWrapper = self.sender()
            sender.editor.deleteLater()  # delete editor
            if sender:
                sender.deleteLater()  # delete wrapper object
        self.stateChanged.emit(state)


class OperationWrapper(QObject):
    """
    Wraps an operation allowing it to be executed as a single command.
    'createAction' will return a QAction which, once triggered, will ask the user to provide
    options if necessary through the option editor. When the operation completes the object will emit
    a 'finished' signal. The result can then be retrieved with the 'output' property
    """
    stateChanged = Signal(str)

    def __init__(self, op: Operation, parent: QObject, editorPosition: QPoint = QPoint()):
        super().__init__(parent)

        self.operation = op
        self.editor: Optional[AbsOperationEditor] = None
        self._editorPos = editorPosition
        self._inputs: Tuple[data.Frame] = tuple()

    def start(self):
        self.editor = self.operation.getEditor()
        self.editor.setWindowTitle(self.operation.name())
        self.editor.acceptAndClose.connect(self.onAcceptEditor)
        # self.editor.rejectAndClose.connect(self.stateChanged())
        self.editor.acceptedTypes = self.operation.acceptedTypes()
        self.editor.inputShapes = [i.shape for i in self._inputs]
        self.editor.setDescription(self.operation.shortDescription(), self.operation.longDescription())
        self.editor.setUpEditor()
        self.editor.workbench = self.operation.workbench
        self.editor.setOptions(*self.operation.getOptions())
        self.editor.setParent(None)
        self.editor.move(self._editorPos)
        self.editor.show()

    @Slot()
    def onAcceptEditor(self) -> None:
        self.stateChanged.emit('start')
        try:
            self.operation.setOptions(*self.editor.getOptions())
        except OptionValidationError as e:
            self.editor.handleErrors(e.invalid)
        else:
            # Prepare worker
            self.__worker = threads.Worker(self.operation, args=self._inputs)
            # Connect
            self.__worker.signals.result.connect(self._onSuccess)
            self.__worker.signals.error.connect(self._onError)
            self.__worker.signals.finished.connect(self._onFinish)
            # Start worker
            QThreadPool.globalInstance().start(self.__worker)
            self.editor.hide()

    @Slot(object, object)
    def _onSuccess(self, _, f: data.Frame) -> None:
        # Signal success
        self.stateChanged.emit('success')
        logging.info('Operation succeeded')

    @Slot(object)
    def _onFinish(self, _) -> None:
        self.stateChanged.emit('finish')
        logging.info('Operation {} finished'.format(self.operation.name()))
        self.__worker = None
        self.editor.close()

    @Slot(object, tuple)
    def _onError(self, _, error: Tuple[type, Exception, str]) -> None:
        self.stateChanged.emit('error')
        msg = str(error[1])
        msg_short = 'Operation failed to execute with following message: <br> {}'.format(msg[:80])
        if len(msg) > 80:
            msg_short += '... (see all in log)'
        msgbox = QMessageBox(QMessageBox.Icon.Critical, 'Critical error', msg_short, QMessageBox.Ok,
                             self.editor)
        logging.error('Operation {} failed with exception {}: {} - trace: {}'.format(
            self.operation.name(), str(error[0]), msg, error[2]))
        msgbox.exec_()
