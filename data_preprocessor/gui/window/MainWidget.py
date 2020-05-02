from PySide2.QtCore import Slot
from PySide2.QtGui import QKeyEvent, Qt
from PySide2.QtWidgets import QTreeView, QListView, QTabWidget, QWidget, QVBoxLayout, \
    QHBoxLayout

from data_preprocessor.data.Workbench import Workbench
from data_preprocessor.flow.OperationDag import OperationDag
from data_preprocessor.gui.graph.controller import GraphController
from data_preprocessor.gui.graph.scene import Scene
from data_preprocessor.gui.graph.view import View
from data_preprocessor.gui.model.WorkbenchModel import WorkbenchModel
from data_preprocessor.gui.widget.OperationMenu import OperationMenu
from data_preprocessor.operation.all import RenameOp, TypeOp


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._workbench = Workbench()
        self.workbench_model = WorkbenchModel(self, self._workbench)
        self.graph = OperationDag()

        class WorkbenchView(QListView):
            def keyPressEvent(self, event: QKeyEvent) -> None:
                if event.key() == Qt.Key_Delete:
                    for index in self.selectedIndexes():
                        self.model().removeRow(index.row())
                else:
                    super().keyPressEvent(event)

        self.__genericView = QTreeView()
        self.__operationMenu = OperationMenu()
        workbenchView = WorkbenchView()
        workbenchView.setModel(self.workbench_model)
        workbenchView.setSelectionMode(QListView.SingleSelection)
        self.workbench_model.rowAppended.connect(workbenchView.edit)
        self.workbench_model.rowAppended.connect(workbenchView.setCurrentIndex)

        tabs = QTabWidget(self)

        # from data_preprocessor.gui.graph2.GraphScene import GraphScene
        # from data_preprocessor.gui.graph2.GraphView import GraphView
        attributeTab = QWidget()
        chartsTab = QWidget()
        # scene = GraphScene(self.graph, self)
        # flowTab = GraphView(self)
        scene = Scene(self)
        flowTab = View(scene)
        controller = GraphController(self.graph, scene, flowTab, self)
        controller.addNode(RenameOp())
        controller.addNode(TypeOp())
        controller.addNode(TypeOp())

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
