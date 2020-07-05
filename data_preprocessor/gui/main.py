import logging

from PySide2.QtCore import Slot, QThreadPool, Qt
from PySide2.QtWidgets import QTabWidget, QWidget, QMainWindow, QMenuBar, QAction, QSplitter, \
    QHBoxLayout

from data_preprocessor.decorators.generic import singleton
from data_preprocessor.flow.OperationDag import OperationDag
from data_preprocessor.gui.attributepanel import AttributePanel
from data_preprocessor.gui.chartpanel import ChartPanel
from data_preprocessor.gui.diffpanel import DataframeSideBySideView, DiffDataframeWidget
from data_preprocessor.gui.framepanel import FramePanel
from data_preprocessor.gui.graph.controller import GraphController
from data_preprocessor.gui.graph.scene import GraphScene
from data_preprocessor.gui.graph.view import GraphView
from data_preprocessor.gui.operationmenu import OperationMenu
from data_preprocessor.gui.statusbar import StatusBar
from data_preprocessor.gui.workbench import WorkbenchModel, WorkbenchView
from data_preprocessor.operation.actionwrapper import OperationAction
from data_preprocessor.operation.loaders import CsvLoader


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbench_model = WorkbenchModel(self)
        self.graph = OperationDag()
        self.operationMenu = OperationMenu()
        self.frameInfoPanel = FramePanel(parent=self,
                                         w=self.workbench_model,
                                         opModel=self.operationMenu.model())
        workbenchView = WorkbenchView()
        workbenchView.setModel(self.workbench_model)
        self.workbench_model.emptyRowInserted.connect(workbenchView.edit)
        self.workbench_model.emptyRowInserted.connect(workbenchView.setCurrentIndex)

        tabs = QTabWidget(self)

        attributeTab = AttributePanel(self.workbench_model, self)
        chartsTab = ChartPanel(self.workbench_model, self)
        scene = GraphScene(self)
        flowTab = GraphView(scene)
        self.controller = GraphController(self.graph, scene, flowTab, self.workbench_model, self)

        tabs.addTab(attributeTab, '&Attribute')
        tabs.addTab(chartsTab, '&Visualise')
        tabs.addTab(flowTab, 'F&low')
        self.__curr_tab = tabs.currentIndex()

        self.__leftSide = QSplitter(Qt.Vertical)
        self.__leftSide.addWidget(self.frameInfoPanel)
        self.__leftSide.addWidget(workbenchView)

        # layout = QHBoxLayout()
        # layout.addWidget(leftSplit, 2)
        # layout.addWidget(tabs, 8)
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self.__leftSide)
        splitter.addWidget(tabs)
        layout = QHBoxLayout(self)
        layout.addWidget(splitter)

        tabs.currentChanged.connect(self.switch_view)
        workbenchView.selectedRowChanged.connect(attributeTab.onFrameSelectionChanged)
        workbenchView.selectedRowChanged.connect(chartsTab.onFrameSelectionChanged)
        workbenchView.selectedRowChanged.connect(self.frameInfoPanel.onFrameSelectionChanged)

    @Slot(int)
    def switch_view(self, tab_index: int) -> None:
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


@singleton
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__activeCount: int = 0  # number of operations in progress
        central_w = MainWidget()
        self.setCentralWidget(central_w)
        self.setStatusBar(StatusBar(self))
        # Initialise a thread pool
        self.threadPool = QThreadPool.globalInstance()
        logging.info('Multithreading with maximum {} threads'.format(self.threadPool.maxThreadCount()))

        menuBar = QMenuBar()
        fileMenu = menuBar.addMenu('File')
        flowMenu = menuBar.addMenu('Flow')
        viewMenu = menuBar.addMenu('View')
        addAction = QAction('Add frame', fileMenu)
        addAction.setStatusTip('Create an empty dataframe in the workbench')
        loadCsvAction = OperationAction(CsvLoader, fileMenu, 'Load csv',
                                        self.rect().center(), central_w.workbench_model)
        compareAction = QAction('Compare dataframes', viewMenu)
        diffAction = QAction('Diff dataframes', viewMenu)
        fileMenu.addAction(addAction)
        fileMenu.addAction(loadCsvAction)
        fileMenu.show()

        exec_flow = QAction('Execute', flowMenu)
        reset_flow = QAction('Reset', flowMenu)
        flowMenu.addAction(exec_flow)
        flowMenu.addAction(reset_flow)
        viewMenu.addAction(compareAction)
        viewMenu.addAction(diffAction)
        flowMenu.show()

        self.setMenuBar(menuBar)

        # Connect
        addAction.triggered.connect(central_w.workbench_model.appendEmptyRow)
        exec_flow.triggered.connect(self.centralWidget().controller.executeFlow)
        reset_flow.triggered.connect(self.centralWidget().controller.resetFlowStatus)
        compareAction.triggered.connect(self.openComparePanel)
        diffAction.triggered.connect(self.openDiffPanel)
        loadCsvAction.stateChanged.connect(self.operationStateChanged)
        self.centralWidget().frameInfoPanel.operationRequest.connect(self.executeOperation)

    @Slot()
    def openComparePanel(self) -> None:
        dv = DataframeSideBySideView(self)
        dv.setWindowFlags(Qt.Window)
        dv.setAttribute(Qt.WA_DeleteOnClose)
        dv.setWindowTitle('Side by side view')
        dv.dataWidgetL.setWorkbench(self.centralWidget().workbench_model)
        dv.dataWidgetR.setWorkbench(self.centralWidget().workbench_model)
        dv.show()

    @Slot()
    def openDiffPanel(self) -> None:
        dv = DiffDataframeWidget(self)
        dv.setWindowFlags(Qt.Window)
        dv.setAttribute(Qt.WA_DeleteOnClose)
        dv.setWindowTitle('Diff view')
        dv.setWorkbench(self.centralWidget().workbench_model)
        dv.show()

    @Slot(int, str)
    def operationStateChanged(self, uid: int, state: str) -> None:
        if state == 'success':
            logging.info('Operation uid={:d} succeeded'.format(uid))
            self.statusBar().showMessage('Operation succeeded', 10000)
        elif state == 'error':
            logging.error('Operation uid={:d} stopped with errors'.format(uid))
            self.statusBar().showMessage('Operation stopped with errors', 10000)
        elif state == 'start':
            self.__activeCount += 1
            self.statusBar().startSpinner()
            logging.info('Operation uid={:d} started'.format(uid))
            self.statusBar().showMessage('Executing...', 10000)
        elif state == 'finish':
            logging.info('Operation uid={:d} finished'.format(uid))
            self.__activeCount -= 1
            if self.__activeCount == 0:
                self.statusBar().stopSpinner()
        # print('Emit', uid, state, 'count={}'.format(self.__activeCount))

    @Slot(type)
    def executeOperation(self, opType: type) -> None:
        action = OperationAction(opType, self, opType.name(),
                                 self.rect().center(), self.centralWidget().workbench_model)
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
