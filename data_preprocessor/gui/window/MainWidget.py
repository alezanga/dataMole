from PySide2.QtGui import QKeyEvent, Qt
from PySide2.QtWidgets import QTreeView, QListView, QTabWidget, QWidget, QVBoxLayout, \
    QHBoxLayout

from data_preprocessor.data.Workbench import Workbench
from data_preprocessor.gui.model.WorkbenchModel import WorkbenchModel


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._workbench = Workbench()
        self.workbench_model = WorkbenchModel(self, self._workbench)

        class WorkbenchView(QListView):
            def keyPressEvent(self, event: QKeyEvent) -> None:
                if event.key() == Qt.Key_Delete:
                    for index in self.selectedIndexes():
                        self.model().removeRow(index.row())
                else:
                    super().keyPressEvent(event)

        genericView = QTreeView()
        workbenchView = WorkbenchView()
        workbenchView.setModel(self.workbench_model)
        workbenchView.setSelectionMode(QListView.SingleSelection)
        self.workbench_model.rowAppended.connect(workbenchView.edit)
        self.workbench_model.rowAppended.connect(workbenchView.setCurrentIndex)

        tabs = QTabWidget(self)

        attributeTab = QWidget()
        chartsTab = QWidget()
        flowTab = QWidget()

        tabs.addTab(attributeTab, 'Attribute')
        tabs.addTab(chartsTab, 'Visualise')
        tabs.addTab(flowTab, 'Flow')

        leftSide = QVBoxLayout()
        leftSide.addWidget(genericView, 0)
        leftSide.addWidget(workbenchView, 0)

        layout = QHBoxLayout()
        layout.addLayout(leftSide, 2)
        layout.addWidget(tabs, 7)

        self.setLayout(layout)
