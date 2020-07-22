from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QComboBox, QFormLayout

from data_preprocessor.gui.charts.scatterplot import ScatterPlotMatrix
from data_preprocessor.gui.charts.timeseriesplot import TimeSeriesPlot


class ChartPanel(QWidget):
    def __init__(self, workbench, parent: QWidget = None):
        super().__init__(parent)
        self.__currentFrameName: str = None
        self.workbenchModel = workbench
        self.__chartTypeCB = QComboBox(self)
        self.fLayout = QFormLayout(self)
        self.fLayout.addRow('Select the type of chart to draw: ', self.__chartTypeCB)
        self.fLayout.setHorizontalSpacing(40)
        self.__chartTypeCB.addItems(['Scatterplot', 'Time series'])
        self.__chartTypeCB.setCurrentIndex(0)
        self.chartSelectionChanged('Scatterplot')
        self.__chartTypeCB.currentTextChanged.connect(self.chartSelectionChanged)

    @Slot(str)
    def chartSelectionChanged(self, text: str) -> None:
        if self.fLayout.rowCount() == 2:
            self.fLayout.removeRow(1)
        if text == 'Scatterplot':
            self.fLayout.addRow(ScatterPlotMatrix(self.workbenchModel, self))
        elif text == 'Time series':
            self.fLayout.addRow(TimeSeriesPlot(self.workbenchModel, self))
        self.onFrameSelectionChanged(self.__currentFrameName)

    @Slot(str, str)
    def onFrameSelectionChanged(self, name: str, *_) -> None:
        self.__currentFrameName = name
        self.fLayout.itemAt(1, QFormLayout.SpanningRole).widget().onFrameSelectionChanged(name)
