from typing import List, Optional, Union, Tuple

import numpy as np
import pandas as pd
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Slot, QPointF, Qt, QModelIndex, QMargins
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QHBoxLayout, QPushButton, \
    QComboBox

from data_preprocessor.data.types import Types
from data_preprocessor.gui.charts.views import SimpleChartView
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, FrameModel, \
    AttributeTableModel, AttributeProxyModel
from data_preprocessor.gui.workbench import WorkbenchModel


class ScatterPlotMatrix(QWidget):

    def __init__(self, workbench: WorkbenchModel, parent=None):
        super().__init__(parent)
        self.__workbench: WorkbenchModel = workbench
        self.__frameModel: FrameModel = None

        # Create widget for the two tables
        sideLayout = QVBoxLayout()
        self.__matrixAttributes = SearchableAttributeTableWidget(self, True, False, False,
                                                                 [Types.Numeric, Types.Ordinal])
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
        self.__comboModel = AttributeProxyModel([Types.String, Types.Ordinal, Types.Nominal], self)

        # Connect
        createButton.clicked.connect(self.showScatterPlots)

    @staticmethod
    def __processCategoricalColumn(df: pd.DataFrame) -> pd.DataFrame:
        """ For every categorical column in 'df' replace categories with their numerical code,
        propagating Nan values. Categorical columns are converted to float """
        categoricalColumns = df.select_dtypes(include='category').columns.to_list()
        if categoricalColumns:
            df = df.copy(True)
            df[categoricalColumns] = \
                df[categoricalColumns].apply(lambda c: c.cat.codes, axis=0).replace(-1, np.nan)
        return df

    @staticmethod
    def __createSeriesFor2Columns(df: pd.DataFrame, xCol: str, yCol: str) -> \
            Tuple[QtCharts.QScatterSeries, QtCharts.QScatterSeries]:
        """ Create two scatter series, the second one with inverted x and y values

        :param df: a dataframe
        :param xCol: the name of the column with X values for plain series
        :param yCol: the name of the column with Y values for plain series
        :return a tuple with the plain series as the first element, and the inverted one as second
        """
        qSeries1 = QtCharts.QScatterSeries()
        points = list(map(lambda t: QPointF(*t), df[[xCol, yCol]].itertuples(index=False, name=None)))
        qSeries1.append(points)

        # Inverted series
        qSeries2 = QtCharts.QScatterSeries()
        points = list(map(lambda qp: QPointF(qp.y(), qp.x()), points))
        qSeries2.append(points)
        return qSeries1, qSeries2

    @staticmethod
    def __createScatterSeries(df: Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy], xCol: str,
                              yCol: str, groupBy: bool) -> \
            Tuple[List[QtCharts.QScatterSeries], List[QtCharts.QScatterSeries]]:
        allSeriesPlain = list()
        allSeriesInverted = list()
        if groupBy:
            df: pd.core.groupby.DataFrameGroupBy
            for groupName, groupedDf in df:
                plain, inverted = ScatterPlotMatrix.__createSeriesFor2Columns(groupedDf, xCol, yCol)
                plain.setName(str(groupName))
                inverted.setName(str(groupName))
                allSeriesPlain.append(plain)
                allSeriesInverted.append(inverted)
        else:
            df: pd.DataFrame
            plain, inverted = ScatterPlotMatrix.__createSeriesFor2Columns(df, xCol, yCol)
            allSeriesPlain.append(plain)
            allSeriesInverted.append(inverted)
        return allSeriesPlain, allSeriesInverted

    @staticmethod
    def __setupChartFromSeries(seriesList: List[QtCharts.QScatterSeries], xAxisName: str,
                               yAxisName: str) -> QtCharts.QChart:
        chart = QtCharts.QChart()
        for series in seriesList:
            series.setMarkerSize(8)
            series.setUseOpenGL(True)
            chart.addSeries(series)
        chart.setDropShadowEnabled(False)
        chart.legend().setVisible(False)
        chart.createDefaultAxes()
        # Add axes names but hide them
        chart.axisX().setTitleText(xAxisName)
        chart.axisY().setTitleText(yAxisName)
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
        # Get index of groupBy Attribute
        group: int = None
        selectedIndex = self.__colorByBox.currentIndex()
        if self.__comboModel.rowCount() > 0 and selectedIndex != -1:
            index: QModelIndex = self.__comboModel.mapToSource(
                self.__comboModel.index(selectedIndex, 0, QModelIndex()))
            group = index.row() if index.isValid() else None

        # Get attributes of interest
        toKeep: List[int] = attributes if group is None else [group, *attributes]
        filterDf = self.__frameModel.frame.getRawFrame().iloc[:, toKeep]
        groupName: Optional[str] = filterDf.columns[0] if group is not None else None
        # Convert categories to numeric, but exclude groupBy attributes since categories are needed there
        processed = self.__processCategoricalColumn(filterDf.iloc[:, 1:] if groupName else filterDf)
        # Save attribute names for later use. Groupby column name is purposely excluded
        attributesColumnNames: List[str] = processed.columns.to_list()
        if groupName:
            df = pd.concat([filterDf.loc[:, groupName], processed], axis=1, ignore_index=False)
            # Group by selected attribute, if present
            df = df.groupby(groupName)
        else:
            df = filterDf

        # Populate the matrix
        for r in range(len(attributes)):
            self.__matrixLayout.setRowStretch(r, 1)
            self.__matrixLayout.setColumnStretch(r, 1)
            for c in range(len(attributes)):
                if r == c:
                    name: str = attributesColumnNames[r]
                    self.__matrixLayout.addWidget(QLabel(name, self), r, c, Qt.AlignCenter)
                elif r < c:
                    xColName: str = attributesColumnNames[c]
                    yColName: str = attributesColumnNames[r]
                    plainSeriesList, invertedSeriesList = \
                        self.__createScatterSeries(df=df, xCol=xColName, yCol=yColName,
                                                   groupBy=bool(groupName))
                    plainChart = ScatterPlotMatrix.__setupChartFromSeries(plainSeriesList,
                                                                          xAxisName=xColName,
                                                                          yAxisName=yColName)
                    invertedChart = ScatterPlotMatrix.__setupChartFromSeries(invertedSeriesList,
                                                                             xAxisName=yColName,
                                                                             yAxisName=xColName)
                    self.__matrixLayout.addWidget(SimpleChartView(plainChart, self), r, c)
                    self.__matrixLayout.addWidget(SimpleChartView(invertedChart, self), c, r)
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
