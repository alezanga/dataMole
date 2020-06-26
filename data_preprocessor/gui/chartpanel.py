from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QComboBox, QFormLayout

from data_preprocessor.gui.charts.scatterplot import ScatterPlotMatrix
from data_preprocessor.gui.charts.timeseriesplot import TimeSeriesPlot


class ChartPanel(QWidget):
    def __init__(self, workbench, parent: QWidget = None):
        super().__init__(parent)
        self.__currentIndex: int = -1
        self.workbench_model = workbench
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
            self.fLayout.addRow(ScatterPlotMatrix(self.workbench_model, self))
        elif text == 'Time series':
            self.fLayout.addRow(TimeSeriesPlot(self.workbench_model, self))
        self.onFrameSelectionChanged(self.__currentIndex)

    @Slot(int)
    def onFrameSelectionChanged(self, index: int) -> None:
        self.__currentIndex = index
        self.fLayout.itemAt(1, QFormLayout.SpanningRole).widget().onFrameSelectionChanged(index)
