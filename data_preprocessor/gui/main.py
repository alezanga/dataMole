from PySide2.QtCore import Slot
from PySide2.QtWidgets import QTreeView, QTabWidget, QWidget, QVBoxLayout, \
    QHBoxLayout, QMainWindow, QMenuBar, QAction

from data_preprocessor.flow.OperationDag import OperationDag
from data_preprocessor.gui.graph.controller import GraphController
from data_preprocessor.gui.graph.scene import Scene
from data_preprocessor.gui.graph.view import View
from data_preprocessor.gui.workbench import WorkbenchModel, WorkbenchView
from data_preprocessor.gui.operation_list import OperationMenu


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbench_model = WorkbenchModel(self)
        self.graph = OperationDag()
        self.__genericView = QTreeView()
        self.__operationMenu = OperationMenu()
        workbenchView = WorkbenchView()
        workbenchView.setModel(self.workbench_model)
        self.workbench_model.rowAppended.connect(workbenchView.edit)
        self.workbench_model.rowAppended.connect(workbenchView.setCurrentIndex)

        tabs = QTabWidget(self)

        attributeTab = QWidget()
        chartsTab = QWidget()
        scene = Scene(self)
        flowTab = View(scene)
        controller = GraphController(self.graph, scene, flowTab, self.workbench_model, self)

        tabs.addTab(attributeTab, 'Attribute')
        tabs.addTab(chartsTab, 'Visualise')
        tabs.addTab(flowTab, 'Flow')
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
            self.__curr_tab = 2
        elif self.__curr_tab == 2 and tab_index != 2:
            self.__leftSide.replaceWidget(self.__operationMenu, self.__genericView)
            self.__curr_tab = tab_index


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        central_w = MainWidget()
        self.setCentralWidget(central_w)

        menu_bar = QMenuBar()
        menu_bar_file = menu_bar.addMenu('File')
        add_action = QAction('Add frame', menu_bar_file)
        add_action.setStatusTip('Create an empty dataframe in the workbench')
        add_action.triggered.connect(central_w.workbench_model.appendRow)
        menu_bar_file.addAction(add_action)
        menu_bar_file.show()

        self.setMenuBar(menu_bar)
