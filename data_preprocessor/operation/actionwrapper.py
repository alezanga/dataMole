import logging
from typing import Optional, Tuple, Dict, Any

from PySide2.QtCore import Slot, QObject, Signal, QPoint, QThreadPool, Qt
from PySide2.QtWidgets import QMessageBox, QAction, QComboBox, QFormLayout, QLabel, QCompleter

from data_preprocessor import data
from data_preprocessor import threads
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from data_preprocessor.gui.editor.optionwidget import TextOptionWidget
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.graph import GraphOperation
from data_preprocessor.operation.interface.operation import Operation
from data_preprocessor.utils import UIdGenerator


class OperationAction(QAction):
    """
    Wraps a single operation allowing to set options through the editor and execute it.
    Emits stateChanged signal when operation starts, succeeds or stops with error.
    Signal parameter can be one of { 'start', 'success', 'error', 'finish' }.
    """

    stateChanged = Signal(int, str)

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
        self.__editorPosition: QPoint = editorPosition
        self.__results: Dict[int, Any] = dict()  # { op_id: result }
        self.triggered.connect(self.startOperation)

    def getResult(self, key: int) -> Any:
        """ Pops the result of operation with specified key if it exists. Otherwise returns None """
        return self.__results.pop(key, None)

    @Slot()
    def startOperation(self) -> None:
        uid: int = UIdGenerator().getUniqueId()
        w = OperationWrapper(self.__operation(*self.__args, **self.__kwargs), uid=uid,
                             parent=self,
                             editorPosition=self.__editorPosition)
        w.wrapperStateChanged.connect(self.onStateChanged)
        w.start()

    @Slot(int, str)
    def onStateChanged(self, uid: int, state: str):
        sender: OperationWrapper = self.sender()
        if state == 'success':
            self.__results[uid] = sender.result
            sender.result = None
        elif state == 'finish':
            sender.editor.deleteLater()  # delete editor
            # sender.deleteLater()  # delete wrapper object
        self.stateChanged.emit(uid, state)


class OperationWrapper(QObject):
    """
    Wraps an operation allowing it to be executed as a single command.
    """
    wrapperStateChanged = Signal(int, str)

    def __init__(self, op: Operation, uid: int, parent: QObject, editorPosition: QPoint = QPoint()):
        super().__init__(parent)

        self.operation = op
        self.uid = uid
        self.editor: Optional[AbsOperationEditor] = None
        self._editorPos = editorPosition
        self._inputs: Tuple[data.Frame] = tuple()
        self.result = None  # hold the result when available
        self._outputNameBox: Optional[TextOptionWidget] = None
        self._inputComboBox: Optional[QComboBox] = None
        self._hasInputOutputOptions: bool = False
        self.__worker: Optional[threads.Worker] = None

    def __setUpInputOutputLayout(self) -> QFormLayout:
        # Add input and output boxes
        self._inputComboBox = QComboBox(self.editor)
        self._inputComboBox.setModel(self.operation.workbench)
        self._outputNameBox = TextOptionWidget(parent=self.editor)
        self._outputNameBox.widget.textChanged.connect(self._validateOutputName)
        self._inputComboBox.currentIndexChanged.connect(self._setInput)
        ioLayout = QFormLayout()
        ioLayout.addRow('Input data:', self._inputComboBox)
        ioLayout.addRow('Output name:', self._outputNameBox)
        completer = QCompleter(self._outputNameBox)
        completer.setModel(self.operation.workbench)
        completer.setFilterMode(Qt.MatchContains)
        completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._outputNameBox.widget.setCompleter(completer)
        return ioLayout

    def start(self):
        if self.operation.needsOptions():
            # Get editor from operation
            self.editor = self.operation.getEditor()
            self.editor.setUpEditor()
            # Notice that this wrapper does setOptions in the editor (since they are one-shot editors)
            self.editor.setParent(None)
        else:
            # Create empty editor
            self.editor = AbsOperationEditor(None)
        # Configure title, description and connect
        self.editor.setWindowTitle(self.operation.name())
        self.editor.setDescription(self.operation.shortDescription(), self.operation.longDescription())
        self.editor.acceptAndClose.connect(self.onAcceptEditor)
        self.editor.rejectAndClose.connect(self.editor.close)
        # If it is a GraphOperation we should add input and output LineEdit
        if isinstance(self.operation, GraphOperation) or not self.operation.needsOptions():
            self._hasInputOutputOptions = True
            ioLayout = self.__setUpInputOutputLayout()
            self.editor.layout().insertLayout(1, ioLayout)
            # Set input to default value (first entry)
            self._setInput(0)
            # Set a default output name (name of input)
            self._outputNameBox.setData(self._inputComboBox.currentText())
        # Set up editor dependencies
        self.operation.injectEditor(self.editor)
        # Show editor
        self.editor.move(self._editorPos)
        self.editor.show()

    @Slot()
    def onAcceptEditor(self) -> None:
        try:
            if self.operation.needsOptions():
                # Validate and set standard options
                options = self.editor.getOptions()
                if isinstance(options, dict):
                    self.operation.setOptions(**options)
                else:
                    self.operation.setOptions(*options)
            if self._hasInputOutputOptions:
                # Validate and set input and output options
                name: str = self._outputNameBox.getData()
                if name is not None:
                    name = name.strip()
                selected: int = self._inputComboBox.currentIndex()
                if not name or selected < 0:
                    raise OptionValidationError([('wrapper', 'Error: output name or input data has not '
                                                             'been selected')])
                self.operation.outName = name
                self.operation.inputIndex = selected
        except OptionValidationError as e:
            self.editor.handleErrors(e.invalid)
        else:
            self.wrapperStateChanged.emit(self.uid, 'start')
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
    def _onSuccess(self, _, f: Any) -> None:
        if self._hasInputOutputOptions:
            # For graph operations result is immediately set in workbench
            self.operation.workbench.setDataframeByName(self.operation.outName, f)
        else:
            # For other operation result is saved and later set in the QAction dictionary
            self.result = f
        # Signal success
        self.wrapperStateChanged.emit(self.uid, 'success')
        logging.info('Operation {} succeeded'.format(self.operation.name()))

    @Slot(object)
    def _onFinish(self) -> None:
        self.__worker = None
        self.editor.close()
        self.wrapperStateChanged.emit(self.uid, 'finish')
        logging.info('Operation {} finished'.format(self.operation.name()))

    @Slot(object, tuple)
    def _onError(self, _, error: Tuple[type, Exception, str]) -> None:
        msg = str(error[1])
        msg_short = 'Operation failed to execute with following message: <br> {}'.format(msg[:80])
        if len(msg) > 80:
            msg_short += '... (see all in log)'
        msgbox = QMessageBox(QMessageBox.Icon.Critical, 'Critical error', msg_short, QMessageBox.Ok,
                             self.editor)
        self.wrapperStateChanged.emit(self.uid, 'error')
        logging.error('Operation {} failed with exception {}: {} - trace: {}'.format(
            self.operation.name(), str(error[0]), msg, error[2]))
        msgbox.exec_()

    @Slot(str)
    def _validateOutputName(self, name: str) -> None:
        if name not in self.operation.workbench.names:
            self._outputNameBox.unsetError()
        else:
            label = QLabel('Warning: variable "{}" will be overwritten'.format(name), self.editor)
            label.setWordWrap(True)
            label.setStyleSheet('color: orange')
            self._outputNameBox.setError(qlabel=label, style='border: 1px solid orange')

    @Slot(int)
    def _setInput(self, index: int) -> None:
        if index is not None and 0 <= index < self.operation.workbench.rowCount():
            fr = self.operation.workbench.getDataframeModelByIndex(index).frame
            self.operation._shapes = [fr.shape]
            self._inputs = (fr,)
            self.operation.injectEditor(self.editor)
