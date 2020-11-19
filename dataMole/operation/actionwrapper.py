# -*- coding: utf-8 -*-
#
# Author:       Alessandro Zangari (alessandro.zangari.code@outlook.com)
# Copyright:    © Copyright 2020 Alessandro Zangari, Università degli Studi di Padova
# License:      GPL-3.0-or-later
# Date:         2020-10-04
# Version:      1.0
#
# This file is part of DataMole.
#
# DataMole is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# DataMole is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DataMole.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Tuple, Dict, Any

from PySide2.QtCore import Slot, QObject, Signal, QPoint, QThreadPool, Qt
from PySide2.QtWidgets import QMessageBox, QAction, QComboBox, QFormLayout, QLabel, QCompleter

from dataMole import data, exceptions as exp, flogging, threads, gui
from dataMole.gui.editor.configuration import configureEditor, configureEditorOptions
from dataMole.gui.editor.interface import AbsOperationEditor
from dataMole.gui.utils import TextOptionWidget
from dataMole.operation.interface.graph import GraphOperation
from dataMole.operation.interface.operation import Operation
from dataMole.utils import UIdGenerator, safeDelete


class OperationAction(QAction):
    """
    Wraps a single operation allowing to set options through the editor and execute it.
    Emits stateChanged signal when operation starts, succeeds or stops with error.
    Signal parameter can be one of { 'start', 'success', 'error', 'finish' }.
    """

    stateChanged = Signal(int, str)
    operationLogger = flogging.OperationLogger(flogging.opsLogger)

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
        # Keep a reference to the currently selected frame when an action is created
        self.__selectedFrame: str = None
        self.__operation: type = op
        self.__editorPosition: QPoint = editorPosition
        self.__results: Dict[int, Any] = dict()  # { op_id: result }
        self.triggered.connect(self.startOperation)

    def setOperationArgs(self, *args, **kwargs) -> None:
        self.__args = args
        self.__kwargs = kwargs

    def setSelectedFrame(self, name: str) -> None:
        """
        Set the frame to be used as input in the editor when it is shown. This is only relevant
        for editors built with the factory. If it not the case you should provide your own parameters
        as operation arguments
        """
        self.__selectedFrame = name

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
        # Pass the selected frame name to the wrapper
        w.selectedFrame = self.__selectedFrame
        w.start()

    @Slot(int, str)
    def onStateChanged(self, uid: int, state: str):
        sender: OperationWrapper = self.sender()
        if state == 'success':
            self.__results[uid] = sender.result
            sender.result = None
        # elif state == 'finish':
        #     sender.editor.deleteLater()  # delete editor (already done)
        #     sender.deleteLater()  # delete wrapper object
        # Log
        if state == 'success' or state == 'error':
            outName = sender.operation.outName if hasattr(sender.operation, 'outName') else None
            inpName = sender.operation.inputName if hasattr(sender.operation, 'inputName') else None
            OperationAction.operationLogger.log(sender.operation, self.__results.get(uid, None),
                                                output=outName,
                                                input=inpName)
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
        self.selectedFrame: str = None  # Set by the action

    def __setUpInputOutputLayout(self) -> QFormLayout:
        # Add input and output boxes
        self._inputComboBox = QComboBox(self.editor)
        self._inputComboBox.setModel(self.operation.workbench)
        self._outputNameBox = TextOptionWidget(parent=self.editor)
        self._outputNameBox.widget.textChanged.connect(self._validateOutputName)
        self._inputComboBox.currentTextChanged.connect(self._changeInputFrame)
        ioLayout = QFormLayout()
        ioLayout.addRow('Input data:', self._inputComboBox)
        ioLayout.addRow('Output name:', self._outputNameBox)
        completer = QCompleter(self._outputNameBox)
        completer.setModel(self.operation.workbench)
        completer.setFilterMode(Qt.MatchContains)
        completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._outputNameBox.widget.setCompleter(completer)
        if self.selectedFrame:
            if self.selectedFrame == self._inputComboBox.currentText():
                # Manually trigger the slot to change input
                self._changeInputFrame(self.selectedFrame)
            else:
                # Set the frame (will trigger _changeInputFrame)
                self._inputComboBox.setCurrentText(self.selectedFrame)
        else:
            # Default to whatever input name is set
            self._changeInputFrame(self._inputComboBox.currentText())
        return ioLayout

    def start(self):
        if self.operation.needsOptions():
            # Get editor from operation
            self.editor = self.operation.getEditor()
            self.editor.setUpEditor()
        else:
            # Create empty editor
            self.editor = AbsOperationEditor()
        configureEditor(self.editor, self.operation, None)
        configureEditorOptions(self.editor, self.operation)
        self.editor.accept.connect(self.onAcceptEditor)
        self.editor.reject.connect(self.cleanUpEditor)
        # If it is a GraphOperation or it has no default editor we should add input and output LineEdit
        if isinstance(self.operation, GraphOperation) or not self.operation.needsOptions():
            self._hasInputOutputOptions = True
            ioLayout = self.__setUpInputOutputLayout()
            self.editor.layout().insertLayout(1, ioLayout)
        # Set up editor dependencies
        self.operation.injectEditor(self.editor)
        # Show editor
        self.editor.move(self._editorPos)
        self.editor.show()

    @Slot()
    def cleanUpEditor(self) -> None:
        # Do not call close() here, since this function is called after a closeEvent
        safeDelete(self.editor)
        self.editor = None

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
                selected: str = self._inputComboBox.currentText()
                if not name or not selected or self._inputComboBox.currentIndex() < 0:
                    raise exp.OptionValidationError(
                        [('wrapper', 'Error: output name or input data has not '
                                     'been selected')])
                self.operation.outName = name
                self.operation.inputName = selected
        except exp.OptionValidationError as e:
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
        flogging.appLogger.info('Operation {} succeeded'.format(self.operation.name()))

    @Slot(object)
    def _onFinish(self) -> None:
        self.__worker = None
        self.cleanUpEditor()
        self.wrapperStateChanged.emit(self.uid, 'finish')
        flogging.appLogger.info('Operation {} finished'.format(self.operation.name()))

    @Slot(object, tuple)
    def _onError(self, _, error: Tuple[type, Exception, str]) -> None:
        msg = str(error[1])
        self.wrapperStateChanged.emit(self.uid, 'error')
        opName = self.operation.name()
        gui.notifier.addMessage('Operation {} failed'.format(opName), msg, QMessageBox.Critical)
        flogging.appLogger.error('Operation {} failed with exception {}: {} - trace: {}'.format(
            opName, str(error[0]), msg, error[2]))

    @Slot(str)
    def _validateOutputName(self, name: str) -> None:
        if name not in self.operation.workbench.names:
            self._outputNameBox.unsetError()
        else:
            label = QLabel('Warning: variable "{}" will be overwritten'.format(name), self.editor)
            label.setWordWrap(True)
            label.setStyleSheet('color: orange')
            self._outputNameBox.setError(qlabel=label, style='border: 1px solid orange')

    @Slot(str)
    def _changeInputFrame(self, frameName: str) -> None:
        if frameName in self.operation.workbench.names:
            fr: data.Frame = self.operation.workbench.getDataframeModelByName(frameName).frame
            outputName: str = self._outputNameBox.getData()
            if not outputName or outputName in self.operation.workbench.names:
                # Change with new name
                self._outputNameBox.setData(frameName)
            self.operation._shapes = self.editor.inputShapes = [fr.shape]
            self._inputs = (fr,)
            self.operation.injectEditor(self.editor)
