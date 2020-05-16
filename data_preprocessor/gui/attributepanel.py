from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QVBoxLayout

from data_preprocessor.gui.frame import FrameModel, AttributeTableModel, SearchableAttributeTableWidget
from data_preprocessor.gui.workbench import WorkbenchModel


class AttributePanel(QWidget):

    def __init__(self, workbench: WorkbenchModel, parent: QWidget = None):
        super().__init__(parent)
        self._workbench: WorkbenchModel = workbench
        self._currentFrameIndex: int = -1
        self._attributeModel: AttributeTableModel = None

        self._attributeTable = SearchableAttributeTableWidget(parent=self, checkable=True, editable=True)
        section2 = QWidget(self)
        section3 = QtCharts.QChartView(self)

        layout = QVBoxLayout()
        layout.addWidget(self._attributeTable, 2)
        layout.addWidget(section2, 1)
        layout.addWidget(section3, 3)
        self.setLayout(layout)

    @Slot(int)
    def selectionChanged(self, frameIndex: int) -> None:
        if 0 <= frameIndex <= self._workbench.rowCount():
            self._currentFrameIndex = frameIndex
            # if not self._attributeModel:
            #     # Create model the first time
            #     self._attributeModel = AttributeTableModel(self, True, True)
            frameModel = self._workbench.getDataframeModelByIndex(frameIndex)
        else:
            self._currentFrameIndex = -1
            frameModel = FrameModel(self)
        self._attributeTable.setSourceFrameModel(frameModel)
        # OLD VERSION (NON SEARCHABLE)
        # Replace frame model
        # self._attributeModel.setSourceFrameModel(frameModel)
        # If model is not set in view yet
        # if self._attributeTable.model() is not self._attributeModel:
        #     self._attributeTable.setModel(self._attributeModel)
        #     hh = self._attributeTable.horizontalHeader()
        #     hh.resizeSection(0, 10)
        #     hh.setSectionResizeMode(0, QHeaderView.Fixed)
        #     hh.setSectionResizeMode(1, QHeaderView.Stretch)
        #     hh.setSectionResizeMode(2, QHeaderView.Fixed)
        #     hh.setStretchLastSection(False)
        #     self._attributeTable.setHorizontalHeader(hh)

        # import time
        # t1 = time.clock()
        # for col in range(1, self._attributeModel.columnCount()):
        #     for row in range(0, self._attributeModel.rowCount()):
        #         data = self._attributeModel.index(row, col, QModelIndex()).data(role=Qt.DisplayRole)
        # t2 = time.clock()
        # logging.debug('Retrieved: {} rows and {} columns'.format(self._attributeModel.rowCount(),
        #                                                          self._attributeModel.columnCount()))
        # logging.debug('TIME ELAPSED: ' + str(t2 - t1))

# class AttributeTableView(QTableView):
#     def mousePressEvent(self, event:QMouseEvent):
#         x = self.columnViewportPosition(0)
#         size = self.columnWidth(0)
#         if x <= event.globalPos().x() <= x+size:
#             self.model().setData(self.model().index())
