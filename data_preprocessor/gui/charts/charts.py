from typing import List

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Slot, QPointF, Qt, QModelIndex, QMargins
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QHBoxLayout, QPushButton, \
    QComboBox

from data_preprocessor.data.types import Types
from data_preprocessor.gui.charts.views import SimpleChartView
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, FrameModel, \
    AttributeTableModel, TypeProxyAttributeModel
from data_preprocessor.gui.workbench import WorkbenchModel


class ScatterPlotMatrix(QWidget):

    def __init__(self, workbench: WorkbenchModel, parent=None):
        super().__init__(parent)
        self.__workbench: WorkbenchModel = workbench
        self.__frameModel: FrameModel = None

        # Create widget for the two tables
        sideLayout = QVBoxLayout()
        self.__matrixAttributes = SearchableAttributeTableWidget(self, True, False, False,
                                                                 [Types.Numeric])
        matrixLabel = QLabel('Select at least two numeric attributes and press \'Create chart\' to plot')
        createButton = QPushButton('Create chart', self)
        self.__colorByBox = QComboBox(self)

        sideLayout.addWidget(matrixLabel)
        sideLayout.addWidget(self.__matrixAttributes)
        sideLayout.addWidget(self.__colorByBox, 1)
        sideLayout.addWidget(createButton, 1)
        self.__matrixLayout: QGridLayout = None
        self.__layout = QHBoxLayout(self)
        self.__layout.addLayout(sideLayout, 1)
        # self.__splitter = QSplitter(self)
        # chartW = QWidget(self)
        # chartW.setLayout(self.__matrixLayout)
        # self.__splitter.addWidget(chartW)
        # sideW = QWidget(self)
        # sideW.setLayout(sideLayout)
        # self.__splitter.addWidget(sideW)
        # self.__layout.addWidget(self.__splitter)
        self.__comboModel = TypeProxyAttributeModel([Types.String, Types.Categorical], self)

        # Connect
        createButton.clicked.connect(self.showScatterPlots)

    # @profile
    def __createScatterPlot(self, xCol: int, yCol: int, groupBy: int = None) -> QtCharts.QChart():
        df = self.__frameModel.frame.getRawFrame()
        # notNanRows = ~df.iloc[:, [xCol, yCol]].isnull().any(axis=1) (series ignore Nans)
        xColS: str = self.__frameModel.shape.col_names[xCol]
        yColS: str = self.__frameModel.shape.col_names[yCol]
        allSeries: List[QtCharts.QScatterSeries] = list()
        if groupBy is not None:
            groupS: str = self.__frameModel.shape.col_names[groupBy]
            categories = df.groupby(groupS)[[xColS, yColS]].apply(lambda x: x.values.tolist())
            i = 0
            for name, values in categories.items():
                series = QtCharts.QScatterSeries()
                series.append(list(map(lambda t: QPointF(*t), values)))
                series.setName(str(name))
                allSeries.append(series)
                i += 1
        else:
            points = list(df.iloc[:, [xCol, yCol]].itertuples(index=False, name=None))
            series = QtCharts.QScatterSeries()
            series.append(list(map(lambda t: QPointF(*t), points)))
            allSeries.append(series)
        chart = QtCharts.QChart()
        for series in allSeries:
            series.setMarkerSize(8)
            series.setUseOpenGL(True)
            chart.addSeries(series)
        chart.setDropShadowEnabled(False)
        chart.legend().setVisible(False)
        chart.createDefaultAxes()
        # Add axes names but hide them
        chart.axisX().setTitleText(xColS)
        chart.axisY().setTitleText(yColS)
        chart.axisX().setTitleVisible(False)
        chart.axisY().setTitleVisible(False)
        # Set font size for axis
        font: QFont = chart.axisX().labelsFont()
        font.setPointSize(9)
        chart.axisX().setLabelsFont(font)
        chart.axisY().setLabelsFont(font)
        chart.setMargins(QMargins(5, 5, 5, 5))
        chart.layout().setContentsMargins(2, 2, 2, 2)
        return chart

    @Slot()
    def showScatterPlots(self) -> None:
        # Clear eventual existing plots
        self.clearScatterPlotMatrix()
        # Create plot with selected attributes
        attributes: List[int] = self.__matrixAttributes.model().checked
        if len(attributes) < 2:
            return
        for r in attributes:
            self.__matrixLayout.setRowStretch(r, 1)
            for c in attributes:
                self.__matrixLayout.setColumnStretch(c, 1)
                if r == c:
                    name: str = self.__frameModel.frame.colnames[r]
                    self.__matrixLayout.addWidget(QLabel(name, self), r, c, Qt.AlignCenter)
                else:
                    group: int = None
                    selectedIndex = self.__colorByBox.currentIndex()
                    if self.__comboModel.rowCount() > 0 and selectedIndex != -1:
                        index: QModelIndex = self.__comboModel.mapToSource(
                            self.__comboModel.index(selectedIndex, 0, QModelIndex()))
                        group = index.row() if index.isValid() else None
                    chart = self.__createScatterPlot(xCol=c, yCol=r, groupBy=group)
                    self.__matrixLayout.addWidget(SimpleChartView(chart, self), r, c)
        self.__matrixLayout.setSpacing(2)

    def clearScatterPlotMatrix(self) -> None:
        if self.__matrixLayout:
            # Delete every child widget
            while self.__matrixLayout.count() > 0:
                child = self.__matrixLayout.itemAt(0).widget()
                if child:
                    self.__matrixLayout.removeWidget(child)
                    child.deleteLater()
            self.__matrixLayout.deleteLater()
        # Create a new grid and add it to main layout
        self.__matrixLayout = QGridLayout()
        self.__layout.insertLayout(0, self.__matrixLayout, 2)

    @Slot(int)
    def onFrameSelectionChanged(self, frameIndex: int) -> None:
        if frameIndex == -1:
            return
        self.__frameModel = self.__workbench.getDataframeModelByIndex(frameIndex)
        self.__matrixAttributes.setSourceFrameModel(self.__frameModel)
        # Combo box
        attributes = AttributeTableModel(self, False, False, False)
        attributes.setFrameModel(self.__frameModel)
        oldModel = self.__comboModel.sourceModel()
        self.__comboModel.setSourceModel(attributes)
        if oldModel:
            oldModel.deleteLater()
        self.__colorByBox.setModel(self.__comboModel)
        # Reset attribute panel
        self.clearScatterPlotMatrix()
