from PySide2.QtCore import Slot
from PySide2.QtWidgets import QTreeView, QTabWidget, QWidget, QVBoxLayout, \
    QHBoxLayout, QMainWindow, QMenuBar, QAction

from data_preprocessor.flow.OperationDag import OperationDag
from data_preprocessor.flow.OperationHandler import OperationHandler
from data_preprocessor.gui.graph.controller import GraphController
from data_preprocessor.gui.graph.scene import Scene
from data_preprocessor.gui.graph.view import View
from data_preprocessor.gui.operation_list import OperationMenu
from data_preprocessor.gui.workbench import WorkbenchModel, WorkbenchView
from data_preprocessor.operation.loaders import CsvLoader
from data_preprocessor.operation.utils import OperationAction


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbench_model = WorkbenchModel(self)
        self.graph = OperationDag()
        self.__genericView = QTreeView()
        self.__operationMenu = OperationMenu()
        workbenchView = WorkbenchView()
        workbenchView.setModel(self.workbench_model)
        self.workbench_model.emptyRowInserted.connect(workbenchView.edit)
        self.workbench_model.emptyRowInserted.connect(workbenchView.setCurrentIndex)

        tabs = QTabWidget(self)

        attributeTab = QWidget()
        chartsTab = QWidget()
        scene = Scene(self)
        flowTab = View(scene)
        controller = GraphController(self.graph, scene, flowTab, self.workbench_model, self)

        tabs.addTab(attributeTab, '&Attribute')
        tabs.addTab(chartsTab, '&Visualise')
        tabs.addTab(flowTab, 'F&low')
        self.__curr_tab = tabs.currentIndex()

        self.__leftSide = QVBoxLayout()
        self.__leftSide.addWidget(self.__genericView, 0)
        self.__leftSide.addWidget(workbenchView, 0)

        layout = QHBoxLayout()
        layout.addLayout(self.__leftSide, 3)
        layout.addWidget(tabs, 7)

        tabs.currentChanged.connect(self.switch_view)

        self.setLayout(layout)

    @Slot(int)
    def switch_view(self, tab_index: int) -> None:
        if tab_index == 2:
            self.__leftSide.replaceWidget(self.__genericView, self.__operationMenu)
            self.__genericView.hide()
            self.__operationMenu.show()
            self.__curr_tab = 2
        elif self.__curr_tab == 2 and tab_index != 2:
            self.__leftSide.replaceWidget(self.__operationMenu, self.__genericView)
            self.__operationMenu.hide()
            self.__genericView.show()
            self.__curr_tab = tab_index


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        central_w = MainWidget()
        self.setCentralWidget(central_w)

        menuBar = QMenuBar()
        fileMenu = menuBar.addMenu('File')
        flowMenu = menuBar.addMenu('Flow')
        addAction = QAction('Add frame', fileMenu)
        addAction.setStatusTip('Create an empty dataframe in the workbench')
        self._loadOpToAction = OperationAction(CsvLoader(None), fileMenu, 'Load csv',
                                               self.rect().center())
        loadCsvAction = self._loadOpToAction.createAction()
        fileMenu.addAction(addAction)
        fileMenu.addAction(loadCsvAction)
        fileMenu.show()

        exec_ac = QAction('Execute', flowMenu)
        flowMenu.addAction(exec_ac)
        flowMenu.show()

        self.setMenuBar(menuBar)

        # Connect
        addAction.triggered.connect(central_w.workbench_model.appendEmptyRow)
        exec_ac.triggered.connect(self.executeFlow)
        self._loadOpToAction.finished.connect(self.loadCsv)

    @Slot()
    def executeFlow(self):
        gr: OperationDag = self.centralWidget().graph
        handler = OperationHandler(gr)
        handler.execute()

    @Slot()
    def loadCsv(self) -> None:
        self.centralWidget().workbench_model.appendNewRow('new_frame', self._loadOpToAction.output)
