import logging

from PySide2.QtCore import Slot, QThreadPool, Qt
from PySide2.QtWidgets import QTabWidget, QWidget, QMainWindow, QMenuBar, QAction, QSplitter, \
    QHBoxLayout

from data_preprocessor.decorators.generic import singleton
from data_preprocessor.flow.OperationDag import OperationDag
from data_preprocessor.gui.attributepanel import AttributePanel
from data_preprocessor.gui.charts.charts import ScatterPlotMatrix
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
        self.__operationMenu = OperationMenu()
        self.__frameInfoPanel = FramePanel(parent=self,
                                           w=self.workbench_model,
                                           opModel=self.__operationMenu.model())
        workbenchView = WorkbenchView()
        workbenchView.setModel(self.workbench_model)
        self.workbench_model.emptyRowInserted.connect(workbenchView.edit)
        self.workbench_model.emptyRowInserted.connect(workbenchView.setCurrentIndex)

        tabs = QTabWidget(self)

        attributeTab = AttributePanel(self.workbench_model, self)
        chartsTab = ScatterPlotMatrix(self.workbench_model, self)
        scene = GraphScene(self)
        flowTab = GraphView(scene)
        self.controller = GraphController(self.graph, scene, flowTab, self.workbench_model, self)

        tabs.addTab(attributeTab, '&Attribute')
        tabs.addTab(chartsTab, '&Visualise')
        tabs.addTab(flowTab, 'F&low')
        self.__curr_tab = tabs.currentIndex()

        self.__leftSide = QSplitter(Qt.Vertical)
        self.__leftSide.addWidget(self.__frameInfoPanel)
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
        workbenchView.selectedRowChanged.connect(self.__frameInfoPanel.onFrameSelectionChanged)
        self.__frameInfoPanel.operationRequest.connect(self.executeOperation)

    @Slot(type)
    def executeOperation(self, opType: type) -> None:
        # TODO
        # action = OperationAction(CsvLoader, fileMenu, 'Load csv',
        #                 self.rect().center(), central_w.workbench_model)
        pass

    @Slot(int)
    def switch_view(self, tab_index: int) -> None:
        if tab_index == 2:
            self.__leftSide.replaceWidget(0, self.__operationMenu)
            self.__frameInfoPanel.hide()
            self.__operationMenu.show()
            self.__curr_tab = 2
        elif self.__curr_tab == 2 and tab_index != 2:
            self.__leftSide.replaceWidget(0, self.__frameInfoPanel)
            self.__operationMenu.hide()
            self.__frameInfoPanel.show()
            self.__curr_tab = tab_index


@singleton
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__started: int = 0  # number of operations in progress
        central_w = MainWidget()
        self.setCentralWidget(central_w)
        self.setStatusBar(StatusBar(self))
        # Initialise a thread pool
        self.threadPool = QThreadPool.globalInstance()
        logging.info('Multithreading with maximum {} threads'.format(self.threadPool.maxThreadCount()))

        menuBar = QMenuBar()
        fileMenu = menuBar.addMenu('File')
        flowMenu = menuBar.addMenu('Flow')
        addAction = QAction('Add frame', fileMenu)
        addAction.setStatusTip('Create an empty dataframe in the workbench')
        loadCsvAction = OperationAction(CsvLoader, fileMenu, 'Load csv',
                                        self.rect().center(), central_w.workbench_model)
        fileMenu.addAction(addAction)
        fileMenu.addAction(loadCsvAction)
        fileMenu.show()

        exec_flow = QAction('Execute', flowMenu)
        reset_flow = QAction('Reset', flowMenu)
        flowMenu.addAction(exec_flow)
        flowMenu.addAction(reset_flow)
        flowMenu.show()

        self.setMenuBar(menuBar)

        # Connect
        addAction.triggered.connect(central_w.workbench_model.appendEmptyRow)
        exec_flow.triggered.connect(self.centralWidget().controller.executeFlow)
        reset_flow.triggered.connect(self.centralWidget().controller.resetFlowStatus)
        loadCsvAction.stateChanged.connect(self.operationStateChanged)

    @Slot(str)
    def operationStateChanged(self, state: str) -> None:
        if state == 'success':
            self.statusBar().showMessage('Operation succeeded', 10000)
        elif state == 'error':
            self.statusBar().showMessage('Operation stopped with errors', 10000)
        elif state == 'start':
            self.__started += 1
            self.statusBar().startSpinner()
            self.statusBar().showMessage('Executing...', 10000)
        elif state == 'finish':
            self.__started -= 1
            if self.__started == 0:
                self.statusBar().stopSpinner()
