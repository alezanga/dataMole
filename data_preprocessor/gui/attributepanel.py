import logging
from typing import Dict, Optional, Tuple, Any

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Slot, Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLayoutItem, QSlider

from data_preprocessor.data.types import Types
from data_preprocessor.gui.frame import FrameModel, SearchableAttributeTableWidget
from data_preprocessor.gui.waitingspinnerwidget import QtWaitingSpinner
from data_preprocessor.gui.workbench import WorkbenchModel


class AttributePanel(QWidget):

    def __init__(self, workbench: WorkbenchModel, parent: QWidget = None):
        super().__init__(parent)
        self._workbench: WorkbenchModel = workbench
        self._frameModel: FrameModel = None
        self.__currentAttributeIndex: int = -1

        self._attributeTable = SearchableAttributeTableWidget(parent=self, checkable=True,
                                                              editable=True, showTypes=True)
        self._statPanel = StatisticsPanel(self)
        self._histPanel = Histogram(self)

        layout = QVBoxLayout()
        layout.addWidget(self._attributeTable, 2)
        layout.addWidget(self._statPanel, 1)
        layout.addWidget(self._histPanel, 3)
        self.setLayout(layout)
        self._attributeTable.tableView.selectedAttributeChanged.connect(self.onAttributeSelectionChanged)
        self._histPanel.slider.valueChanged.connect(self.onHistSliderChange)
        self._histPanel.slider.setEnabled(False)
        self._histPanel.label.setEnabled(False)

    @Slot(int)
    def onFrameSelectionChanged(self, frameIndex: int) -> None:
        if self._frameModel:
            # Disconnect everything from old model
            self._frameModel.disconnect(self)
        assert 0 <= frameIndex < self._workbench.rowCount()
        self._frameModel = self._workbench.getDataframeModelByIndex(frameIndex)
        self._attributeTable.setSourceFrameModel(self._frameModel)
        # Reconnect new model
        self._frameModel.statisticsComputed.connect(self.onComputationFinished)
        # Reset attribute panel
        self.onAttributeSelectionChanged(-1)

    @Slot(int)
    def onAttributeSelectionChanged(self, attributeIndex: int) -> None:
        if self.__currentAttributeIndex == attributeIndex:
            return
        # Set working attribute and its type
        self.__currentAttributeIndex = attributeIndex
        if self.__currentAttributeIndex == -1:
            self._statPanel.setStatistics(dict())
            self._histPanel.setData(dict())
            return
        attType = self._frameModel.headerData(attributeIndex, Qt.Horizontal,
                                              FrameModel.DataRole.value)[1]
        stat: Optional[Dict[str, object]] = self._frameModel.statistics.get(
            self.__currentAttributeIndex, None)
        if not stat:
            # Ask the model to compute statistics
            self._statPanel.spinner.start()
            self._frameModel.computeStatistics(attribute=self.__currentAttributeIndex)
            logging.debug('Attribute changed and computation statistics started')
        else:
            self.onComputationFinished(identifier=(self.__currentAttributeIndex, attType, 'stat'))
        hist: Optional[Dict[Any, int]] = self._frameModel.histogram.get(self.__currentAttributeIndex,
                                                                        None)
        if not hist:
            self.onHistSliderChange(self._histPanel.slider.value())
        else:
            self.onComputationFinished(identifier=(self.__currentAttributeIndex, attType, 'hist'))
        # Connect slider if type is numeric
        if attType == Types.Numeric:
            self._histPanel.slider.setEnabled(True)
            self._histPanel.label.setEnabled(True)
            self._histPanel.slider.setToolTip('Number of bins')
        else:
            self._histPanel.slider.setDisabled(True)
            self._histPanel.label.setDisabled(True)
            self._histPanel.slider.setToolTip('Bin number is not allowed for non numeric attributes')

    @Slot(int)
    def onHistSliderChange(self, value: int) -> None:
        # Ask the model to compute histogram data
        self._histPanel.label.setText('Number of bins: {:d}'.format(value))
        self._histPanel.spinner.start()
        self._frameModel.computeHistogram(attribute=self.__currentAttributeIndex,
                                          histBins=value)
        logging.debug('Slider changed and computation of histogram data started')

    @Slot(tuple)
    def onComputationFinished(self, identifier: Tuple[int, Types, str]) -> None:
        attributeIndex, attributeType, mode = identifier
        if self.__currentAttributeIndex != attributeIndex:
            return
        if mode == 'stat':
            stat: Dict[str, object] = self._frameModel.statistics.get(attributeIndex)
            self._statPanel.spinner.stop()
            self._statPanel.setStatistics(stat)
            logging.debug('Attribute changed and statistics set: {}'.format(stat))
        elif mode == 'hist':
            hist: Dict[Any, int] = self._frameModel.histogram.get(attributeIndex)
            self._histPanel.spinner.stop()
            self._histPanel.setData(hist)
            logging.debug('Histogram data set')


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


class Histogram(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.spinner = QtWaitingSpinner(parent=self, centerOnParent=True,
                                        disableParentWhenSpinning=True)
        self.layout = QVBoxLayout()
        self.chartView = QtCharts.QChartView(self)
        self.chart = None
        self.slider = QSlider(orientation=Qt.Horizontal, parent=self)
        self.slider.setValue(20)
        self.slider.setMinimum(2)
        self.slider.setMaximum(100)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setPageStep(1)
        self.slider.setSingleStep(1)
        self.slider.setTracking(False)
        self.label = QLabel('Number of bins: {:d}'.format(self.slider.value()))
        self.layout.addWidget(self.chartView)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.slider)
        self.setLayout(self.layout)

    def clearChart(self) -> None:
        if self.chart:
            self.chartView.setChart(QtCharts.QChart())
            self.chart.deleteLater()
            self.chart = None

    def setData(self, data: Dict[Any, int]):
        self.clearChart()
        if not data:
            return
        barSet = QtCharts.QBarSet('Frequency')
        frequencies = [f for f in data.values()]
        barSet.append(frequencies)
        series = QtCharts.QBarSeries()
        series.append(barSet)
        chart = QtCharts.QChart()
        chart.addSeries(series)
        chart.setTitle('Value frequency ({} bins)'.format(len(frequencies)))
        chart.setAnimationOptions(QtCharts.QChart.SeriesAnimations)

        axisX = QtCharts.QBarCategoryAxis()
        axisX.append(['{:.2f}'.format(k) if isinstance(k, float) else str(k) for k in data.keys()])
        axisX.setLabelsAngle(30)
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = QtCharts.QValueAxis()
        axisY.setRange(0, max(frequencies) + 1)
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        chart.legend().setVisible(False)

        self.chart = chart
        self.chartView.setChart(self.chart)
