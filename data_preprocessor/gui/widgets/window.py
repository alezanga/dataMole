import logging
import os

from PySide2 import QtGui
from PySide2.QtCore import Slot, QThreadPool, Qt, QModelIndex, QUrl, QMutex
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QTabWidget, QWidget, QMainWindow, QMenuBar, QAction, QSplitter, \
    QHBoxLayout, QMenu

from data_preprocessor import flow, flogging, gui
from data_preprocessor.gui.graph import GraphController, GraphView, GraphScene
from data_preprocessor.gui.widgets.attributepanel import AttributePanel
from data_preprocessor.gui.widgets.chartpanel import ChartPanel
from data_preprocessor.gui.widgets.diffpanel import DataframeSideBySideView
from data_preprocessor.gui.widgets.framepanel import FramePanel
from data_preprocessor.gui.widgets.operationmenu import OperationMenu
from data_preprocessor.gui.workbench import WorkbenchModel, WorkbenchView
from data_preprocessor.operation.actionwrapper import OperationAction
from data_preprocessor.operation.readwrite.csv import CsvLoader, CsvWriter
from data_preprocessor.operation.readwrite.pickle import PickleLoader, PickleWriter


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbenchModel = WorkbenchModel(self)
        self.graph = flow.dag.OperationDag()
        self.operationMenu = OperationMenu()
        self.frameInfoPanel = FramePanel(parent=self,
                                         w=self.workbenchModel,
                                         opModel=self.operationMenu.model())
        self.workbenchView = WorkbenchView()
        self.workbenchView.setModel(self.workbenchModel)
        self.workbenchModel.emptyRowInserted.connect(self.workbenchView.startEditNoSelection)

        tabs = QTabWidget(self)

        attributeTab = AttributePanel(self.workbenchModel, self)
        chartsTab = ChartPanel(self.workbenchModel, self)
        scene = GraphScene(self)
        self._flowView = GraphView(scene, self)
        self.controller = GraphController(self.graph, scene, self._flowView, self.workbenchModel, self)

        tabs.addTab(attributeTab, '&Attribute')
        tabs.addTab(chartsTab, '&Visualise')
        tabs.addTab(self._flowView, 'F&low')
        self.__curr_tab = tabs.currentIndex()

        self.__leftSide = QSplitter(Qt.Vertical)
        self.__leftSide.addWidget(self.frameInfoPanel)
        self.__leftSide.addWidget(self.workbenchView)

        # layout = QHBoxLayout()
        # layout.addWidget(leftSplit, 2)
        # layout.addWidget(tabs, 8)
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self.__leftSide)
        splitter.addWidget(tabs)
        layout = QHBoxLayout(self)
        layout.addWidget(splitter)

        tabs.currentChanged.connect(self.changeTabsContext)
        self.workbenchView.selectedRowChanged[str, str].connect(attributeTab.onFrameSelectionChanged)
        self.workbenchView.selectedRowChanged[str, str].connect(chartsTab.onFrameSelectionChanged)
        self.workbenchView.selectedRowChanged[str, str].connect(
            self.frameInfoPanel.onFrameSelectionChanged)
        self.workbenchView.rightClick.connect(self.createWorkbenchPopupMenu)

    @Slot(int)
    def changeTabsContext(self, tab_index: int) -> None:
        if tab_index == 2:
            self.__leftSide.replaceWidget(0, self.operationMenu)
            self.frameInfoPanel.hide()
            self.operationMenu.show()
            self.__curr_tab = 2
        elif self.__curr_tab == 2 and tab_index != 2:
            self.__leftSide.replaceWidget(0, self.frameInfoPanel)
            self.operationMenu.hide()
            self.frameInfoPanel.show()
            self.__curr_tab = tab_index

    @Slot(QModelIndex)
    def createWorkbenchPopupMenu(self, index: QModelIndex) -> None:
        # Create a popup menu when workbench is right-clicked over a valid frame name
        # Menu display delete and remove options
        frameName: str = index.data(Qt.DisplayRole)
        pMenu = QMenu(self)
        # Reuse MainWindow actions
        csvAction = self.parentWidget().aWriteCsv
        pickleAction = self.parentWidget().aWritePickle
        # Set correct args for the clicked row
        csvAction.setOperationArgs(w=self.workbenchModel, frameName=frameName)
        pickleAction.setOperationArgs(w=self.workbenchModel, frameName=frameName)
        deleteAction = QAction('Remove', pMenu)
        deleteAction.triggered.connect(lambda: self.workbenchModel.removeRow(index.row()))
        pMenu.addActions([csvAction, pickleAction, deleteAction])
        pMenu.popup(QtGui.QCursor.pos())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__activeCount: int = 0  # number of operations in progress
        centralWidget = MainWidget()
        self.setCentralWidget(centralWidget)
        self.notifier = None  # Set by main script
        # Initialise a thread pool
        self.threadPool = QThreadPool.globalInstance()
        logging.info('Multithreading with maximum {} threads'.format(self.threadPool.maxThreadCount()))
        self.setWindowTitle('dataMole')

        self.setUpMenus()
        self.__spinnerMutex = QMutex()

        centralWidget.frameInfoPanel.operationRequest.connect(self.executeOperation)
        centralWidget.workbenchView.selectedRowChanged[str, str].connect(self.changedSelectedFrame)

    def moveEvent(self, event: QtGui.QMoveEvent) -> None:
        self.notifier.mNotifier.updatePosition()
        super().moveEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.notifier.mNotifier.updatePosition()
        super().resizeEvent(event)

    @Slot()
    def openComparePanel(self) -> None:
        w = self.centralWidget().workbenchModel
        dv = DataframeSideBySideView(self)
        dv.setWindowFlags(Qt.Window)
        dv.setAttribute(Qt.WA_DeleteOnClose)
        dv.setWindowTitle('Side by side view')
        dv.dataWidgetL.setWorkbench(w)
        dv.dataWidgetR.setWorkbench(w)
        if w.rowCount():
            dv.dataWidgetL.setDataframe(dv.dataWidgetL.inputCB.currentText())
            dv.dataWidgetR.setDataframe(dv.dataWidgetR.inputCB.currentText())
        dv.show()

    # @Slot()
    # def openDiffPanel(self) -> None:
    #     TODO: remove this?
    #     dv = DiffDataframeWidget(self)
    #     dv.setWindowFlags(Qt.Window)
    #     dv.setAttribute(Qt.WA_DeleteOnClose)
    #     dv.setWindowTitle('Diff view')
    #     dv.setWorkbench(self.centralWidget().workbenchModel)
    #     dv.show()

    @Slot(str, str)
    def changedSelectedFrame(self, newName: str, _: str) -> None:
        # Slot called when workbench selection change
        self.aWriteCsv.setOperationArgs(w=self.centralWidget().workbenchModel, frameName=newName)
        self.aWritePickle.setOperationArgs(w=self.centralWidget().workbenchModel, frameName=newName)

    @Slot(int, str)
    def operationStateChanged(self, uid: int, state: str) -> None:
        if state == 'success':
            logging.info('Operation uid={:d} succeeded'.format(uid))
            self.statusBar().showMessage('Operation succeeded', 10000)
        elif state == 'error':
            logging.error('Operation uid={:d} stopped with errors'.format(uid))
            self.statusBar().showMessage('Operation stopped with errors', 10000)
        elif state == 'start':
            self.__spinnerMutex.lock()
            self.__activeCount += 1
            self.__spinnerMutex.unlock()
            self.statusBar().startSpinner()
            logging.info('Operation uid={:d} started'.format(uid))
            self.statusBar().showMessage('Executing...', 10000)
        elif state == 'finish':
            logging.info('Operation uid={:d} finished'.format(uid))
            self.__spinnerMutex.lock()
            self.__activeCount -= 1
            if self.__activeCount == 0:
                self.statusBar().stopSpinner()
            self.__spinnerMutex.unlock()
        # print('Emit', uid, state, 'count={}'.format(self.__activeCount))

    @Slot(type)
    def executeOperation(self, opType: type) -> None:
        action = OperationAction(opType, self, opType.name(),
                                 self.rect().center(), self.centralWidget().workbenchModel)
        # Set selected frame in the input combo box of the action
        selection = self.centralWidget().workbenchView.selectedIndexes()
        if selection:
            selectedFrame: str = selection[0].data(Qt.DisplayRole)
            action.setSelectedFrame(selectedFrame)
        # Delete action when finished
        action.stateChanged.connect(self.operationStateChanged)
        action.stateChanged.connect(self.deleteAction)
        # Start operation
        action.trigger()

    @Slot(int, str)
    def deleteAction(self, uid: int, state: str):
        if state == 'finish':
            action: QAction = self.sender()
            action.deleteLater()
            logging.info('Action for operation uid={:d} scheduled for deletion'.format(uid))

    def setUpMenus(self) -> None:
        menuBar = QMenuBar()
        fileMenu = menuBar.addMenu('File')
        importMenu = fileMenu.addMenu('Import')
        exportMenu = fileMenu.addMenu('Export')
        flowMenu = menuBar.addMenu('Flow')
        viewMenu = menuBar.addMenu('View')
        helpMenu = menuBar.addMenu('Help')
        aAppendEmpty = QAction('Add frame', fileMenu)
        aAppendEmpty.setStatusTip('Create an empty dataframe in the workbench')
        aQuit = QAction('Quit', fileMenu)
        aLoadCsv = OperationAction(CsvLoader, fileMenu, 'From csv',
                                   self.rect().center(), self.centralWidget().workbenchModel)
        self.aWriteCsv = OperationAction(CsvWriter, fileMenu, 'To csv', self.rect().center(),
                                         w=self.centralWidget().workbenchModel)
        aLoadPickle = OperationAction(PickleLoader, fileMenu, 'From pickle', self.rect().center(),
                                      self.centralWidget().workbenchModel)
        self.aWritePickle = OperationAction(PickleWriter, fileMenu, 'To pickle',
                                            self.mapToGlobal(self.rect().center()),
                                            w=self.centralWidget().workbenchModel)
        aCompareFrames = QAction('Compare dataframes', viewMenu)
        aLogDir = QAction('Open log directory', helpMenu)
        aClearLogs = QAction('Delete old logs', helpMenu)
        fileMenu.addActions([aAppendEmpty, aQuit])
        exportMenu.addActions([self.aWriteCsv, self.aWritePickle])
        importMenu.addActions([aLoadCsv, aLoadPickle])

        aStartFlow = QAction('Execute', flowMenu)
        aResetFlow = QAction('Reset', flowMenu)
        flowMenu.addAction(aStartFlow)
        flowMenu.addAction(aResetFlow)
        viewMenu.addAction(aCompareFrames)
        helpMenu.addActions([aLogDir, aClearLogs])

        self.setMenuBar(menuBar)

        # Tips
        aLoadCsv.setStatusTip('Load a csv file in the workbench')
        aLoadPickle.setStatusTip('Load a Pickle file in the workbench')
        self.aWriteCsv.setStatusTip('Write a dataframe to a csv file')
        self.aWritePickle.setStatusTip('Serializes a dataframe into a pickle file')
        aCompareFrames.setStatusTip('Open two dataframes side by side')
        aStartFlow.setStatusTip('Start flow-graph execution')
        aResetFlow.setStatusTip('Reset the node status in flow-graph')
        aLogDir.setStatusTip('Open the folder containing all logs')
        aClearLogs.setStatusTip('Delete older logs and keep the last 5')

        # Connect
        aAppendEmpty.triggered.connect(self.centralWidget().workbenchModel.appendEmptyRow)
        aQuit.triggered.connect(self.close)
        aStartFlow.triggered.connect(self.centralWidget().controller.executeFlow)
        aResetFlow.triggered.connect(self.centralWidget().controller.resetFlowStatus)
        aCompareFrames.triggered.connect(self.openComparePanel)
        aLogDir.triggered.connect(self.openLogDirectory)
        aClearLogs.triggered.connect(self.clearLogDir)

        aLoadCsv.stateChanged.connect(self.operationStateChanged)
        aLoadPickle.stateChanged.connect(self.operationStateChanged)
        self.aWriteCsv.stateChanged.connect(self.operationStateChanged)
        self.aWritePickle.stateChanged.connect(self.operationStateChanged)

    @Slot()
    def openLogDirectory(self) -> None:
        QDesktopServices.openUrl(QUrl(os.path.join(os.getcwd(), flogging.LOG_FOLDER)))

    @Slot()
    def clearLogDir(self) -> None:
        flogging.deleteOldLogs()
        gui.statusBar.showMessage('Logs cleared')
