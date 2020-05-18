import logging
from typing import Dict, Optional

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Slot, Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLayoutItem

from data_preprocessor.gui.frame import FrameModel, SearchableAttributeTableWidget
from data_preprocessor.gui.waitingspinnerwidget import QtWaitingSpinner
from data_preprocessor.gui.workbench import WorkbenchModel


class AttributePanel(QWidget):

    def __init__(self, workbench: WorkbenchModel, parent: QWidget = None):
        super().__init__(parent)
        self._workbench: WorkbenchModel = workbench
        self._frameModel: FrameModel = None
        self._currentFrameIndex: int = -1

        self._attributeTable = SearchableAttributeTableWidget(parent=self, checkable=True, editable=True)
        self._statPanel = StatisticsPanel(self)
        section3 = QtCharts.QChartView(self)

        layout = QVBoxLayout()
        layout.addWidget(self._attributeTable, 2)
        layout.addWidget(self._statPanel, 1)
        layout.addWidget(section3, 3)
        self.setLayout(layout)
        self._attributeTable.tableView.selectedAttributeChanged.connect(self.attributeChanged)

    @Slot(int)
    def selectionChanged(self, frameIndex: int) -> None:
        if 0 <= frameIndex < self._workbench.rowCount():
            self._currentFrameIndex = frameIndex
            # if not self._attributeModel:
            #     # Create model the first time
            #     self._attributeModel = AttributeTableModel(self, True, True)
            self._frameModel = self._workbench.getDataframeModelByIndex(frameIndex)
        else:
            self._currentFrameIndex = -1
            self._frameModel = FrameModel(self)
        self._attributeTable.setSourceFrameModel(self._frameModel)

    @Slot(str)
    def attributeChanged(self, attributeName: str) -> None:
        if not attributeName:
            return
        s: Optional[Dict[str, object]] = self._frameModel.statistics.get(attributeName, None)
        if not s:
            # Ask the model to compute statistics
            self._statPanel.spinner.start()
            self._frameModel.computeStatistics(attribute=attributeName)
            self._frameModel.statisticsComputed.connect(self.attributeChanged)
            logging.debug('Attribute changed and computation statistics started')
        else:
            # Statistics are computed, just show them
            self._statPanel.spinner.stop()
            self._statPanel.setStatistics(s)
            logging.debug('Attribute changed and statistics set: {}'.format(s))


class StatisticsPanel(QWidget):
    _MAX_STAT_ROW = 3

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.spinner = QtWaitingSpinner(parent=self, centerOnParent=True,
                                        disableParentWhenSpinning=True)

        self.spinner.setInnerRadius(15)
        self.layout = QGridLayout()
        self.layout.setHorizontalSpacing(2)
        self.layout.setVerticalSpacing(4)
        self.setLayout(self.layout)

    def setStatistics(self, stat: Dict[str, object]) -> None:
        item: QLayoutItem = self.layout.takeAt(0)
        while item:
            item.widget().deleteLater()
            self.layout.removeItem(item)
            item = self.layout.takeAt(0)
        r: int = 0
        c: int = 0
        for k, v in stat.items():
            self.layout.addWidget(QLabel('{}:'.format(k), self), r, c, 1, 1,
                                  alignment=Qt.AlignLeft)
            self.layout.addWidget(QLabel('{}'.format(str(v)), self), r, c + 1, 1, 1,
                                  alignment=Qt.AlignLeft)
            r += 1
            if r % StatisticsPanel._MAX_STAT_ROW == 0:
                self.layout.setColumnMinimumWidth(c + 2, 5)  # separator
                c += 3
                r = 0
