from typing import Dict, Optional, Tuple, Any

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLayoutItem, QSlider, \
    QPushButton, QSizePolicy, QMessageBox

from data_preprocessor import flogging, gui
from data_preprocessor.data.types import Types, Type
from data_preprocessor.gui.charts.views import InteractiveChartView
from data_preprocessor.gui.diffpanel import DataframeView
from data_preprocessor.gui.mainmodels import FrameModel, SearchableAttributeTableWidget
from data_preprocessor.gui.waitingspinnerwidget import QtWaitingSpinner
from data_preprocessor.gui.workbench import WorkbenchModel
from data_preprocessor.operation.utils import isFloat


class AttributePanel(QWidget):

    def __init__(self, workbench: WorkbenchModel, parent: QWidget = None):
        super().__init__(parent)
        self._workbench: WorkbenchModel = workbench
        self._frameModel: FrameModel = None
        self.__currentAttributeIndex: int = -1

        self._attributeTable = SearchableAttributeTableWidget(parent=self, checkable=False,
                                                              editable=True, showTypes=True)
        self._statPanel = StatisticsPanel(self)
        self._histPanel = Histogram(self)

        layout = QVBoxLayout()
        layout.addWidget(self._attributeTable, 2)
        layout.addWidget(self._statPanel, 1)
        layout.addWidget(self._histPanel, 3)
        self.setLayout(layout)
        self._attributeTable.tableView.selectedRowChanged[int, int].connect(
            self.onAttributeSelectionChanged)
        self._histPanel.slider.valueChanged.connect(self.recomputeHistogram)
        self._histPanel.slider.setEnabled(False)
        self._histPanel.label.setEnabled(False)

        # Add view frame
        viewButton = QPushButton('View as dataframe', self)
        viewButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._attributeTable.layout().itemAt(0).layout().insertWidget(0, viewButton, 1, Qt.AlignLeft)
        viewButton.clicked.connect(self.viewFrame)

    @Slot(str, str)
    def onFrameSelectionChanged(self, frameName: str, *_) -> None:
        if not frameName:
            return
        if self._frameModel:
            # Disconnect everything from old model
            self._frameModel.disconnect(self)
        self._frameModel = self._workbench.getDataframeModelByName(frameName)
        self._attributeTable.setSourceFrameModel(self._frameModel)
        # Reconnect new model
        self._frameModel.statisticsComputed.connect(self.onComputationFinished)
        self._frameModel.statisticsError.connect(self.onComputationError)
        # Reset attribute panel
        self.onAttributeSelectionChanged(-1)

    @Slot(int, int)
    def onAttributeSelectionChanged(self, attributeIndex: int, *_) -> None:
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
            flogging.appLogger.debug('Attribute changed and statistics computation started')
        else:
            self.onComputationFinished(identifier=(self.__currentAttributeIndex, attType, 'stat'))
        hist: Optional[Dict[Any, int]] = self._frameModel.histogram.get(self.__currentAttributeIndex,
                                                                        None)
        if not hist:
            self.recomputeHistogram(self._histPanel.slider.value())
            flogging.appLogger.debug('Attribute changed and histogram computation started')
        else:
            self.onComputationFinished(identifier=(self.__currentAttributeIndex, attType, 'hist'))
        # Connect slider if type is numeric
        if attType == Types.Numeric or attType == Types.Datetime:
            self._histPanel.slider.setEnabled(True)
            self._histPanel.label.setEnabled(True)
            self._histPanel.slider.setToolTip('Number of bins')
        else:
            self._histPanel.slider.setDisabled(True)
            self._histPanel.label.setDisabled(True)
            self._histPanel.slider.setToolTip('Bin number is not allowed for non continuous attributes')

    @Slot(int)
    def recomputeHistogram(self, bins: int) -> None:
        # Ask the model to compute histogram data
        self._histPanel.label.setText('Number of bins: {:d}'.format(bins))
        self._histPanel.spinner.start()
        self._frameModel.computeHistogram(attribute=self.__currentAttributeIndex,
                                          histBins=bins)
        flogging.appLogger.debug('recomputeHistogram() called: computation of histogram data started')

    @Slot(tuple)
    def onComputationFinished(self, identifier: Tuple[int, Type, str]) -> None:
        attributeIndex, attributeType, mode = identifier
        if self.__currentAttributeIndex != attributeIndex:
            return
        if mode == 'stat':
            stat: Dict[str, object] = self._frameModel.statistics.get(attributeIndex)
            self._statPanel.spinner.stop()
            self._statPanel.setStatistics(stat)
            flogging.appLogger.debug('Statistics set: {}'.format(stat))
        elif mode == 'hist':
            hist: Dict[Any, int] = self._frameModel.histogram.get(attributeIndex)
            self._histPanel.spinner.stop()
            self._histPanel.setData(hist, asRanges=(identifier[1] == Types.Numeric or identifier[1] ==
                                                    Types.Datetime))
            # Ensure slider label and value are correctly set
            self._histPanel.slider.blockSignals(True)
            self._histPanel.slider.setValue(len(hist))
            self._histPanel.slider.blockSignals(False)
            self._histPanel.label.setText('Number of bins: {:d}'.format(len(hist)))
            if self._histPanel.chart:
                self._histPanel.chartView.setBestTickCount(self._histPanel.chart.size())
            flogging.appLogger.debug('Histogram data set')

    @Slot(tuple)
    def onComputationError(self, identifier: Tuple[int, Type, str]) -> None:
        attributeIndex, attributeType, mode = identifier
        # Send a notification
        modeStr = 'histogram' if mode == 'hist' else 'statistics'
        gui.notifier.addMessage('Update error', 'An internal error occurred while '
                                                'updating column {}'.format(modeStr),
                                QMessageBox.Critical)
        # Stop spinner
        if self.__currentAttributeIndex != attributeIndex:
            return
        if mode == 'stat':
            self._statPanel.spinner.stop()
        elif mode == 'hist':
            self._histPanel.spinner.stop()

    @Slot()
    def viewFrame(self) -> None:
        if not self._frameModel:
            return
        w = DataframeView(self)
        w.setAttribute(Qt.WA_DeleteOnClose)
        w.setWindowFlags(Qt.Window)
        w.setWindowTitle('Dataframe view')
        w.setWorkbench(self._workbench)
        w.inputCB.setCurrentText(self._frameModel.name)
        if not w.dataView.model() or w.dataView.model().sourceModel() is not self._frameModel:
            # If the input change was not triggered then you have to update it manually
            # May happen if currentText == frameModel.name
            w.setDataframe(self._frameModel.name)
        w.show()


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
        self.chartView = InteractiveChartView(parent=self)
        self.chartView.enablePan(False)
        self.chartView.enableKeySequences(False)
        self.chartView.enableZoom(False)
        self.chartView.enableCallout(False)  # Callout doesn't work
        self.chartView.enableInWindow(False)
        self.chartView.enablePositionTracker(False)
        self.chart = None
        self.slider = QSlider(orientation=Qt.Horizontal, parent=self)
        self.currentBinN: int = -1
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

    def setData(self, data: Dict[Any, int], asRanges: bool = False):
        self.clearChart()
        if not data:
            return
        barSet = QtCharts.QBarSet('Frequency')
        frequencies = [f for f in data.values()]
        self.currentBinN = len(frequencies)
        barSet.append(frequencies)
        series = QtCharts.QBarSeries()
        series.append(barSet)
        chart = QtCharts.QChart()
        chart.addSeries(series)
        chart.setTitle('Value frequency ({} bins)'.format(self.currentBinN))
        chart.setAnimationOptions(QtCharts.QChart.SeriesAnimations)

        labels = ['{:.2f}'.format(k) if isinstance(k, float) else str(k) for k in data.keys()]
        if asRanges:
            if isFloat(labels[0]):
                # Assume labels are float
                lastEnd = float(labels[-1]) + (float(labels[1]) - float(labels[0]))
                labels.append('{:.2f}'.format(lastEnd))
            axisX = QtCharts.QCategoryAxis()
            for i in range(len(labels) - 1):
                axisX.append(labels[i + 1], (i + 1) * 2 * series.barWidth())
            axisX.setStartValue(0)
            axisX.setLabelsPosition(QtCharts.QCategoryAxis.AxisLabelsPositionCenter)
        else:
            axisX = QtCharts.QBarCategoryAxis()
            axisX.append(labels)
        # Set font
        font: QFont = axisX.labelsFont()
        font.setPointSize(11)
        axisX.setLabelsFont(font)
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = QtCharts.QValueAxis()
        axisY.setRange(0, max(frequencies) + 1)
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        chart.legend().setVisible(False)

        self.chart = chart
        self.chartView.setChart(self.chart)
