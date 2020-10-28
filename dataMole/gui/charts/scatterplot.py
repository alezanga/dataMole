# -*- coding: utf-8 -*-
#
# Author:       Alessandro Zangari (alessandro.zangari.code@outlook.com)
# Copyright:    © Copyright 2020 Alessandro Zangari, Università degli Studi di Padova
# License:      GPL-3.0-or-later
# Date:         2020-10-04
# Version:      1.0
#
# This file is part of DataMole.
#
# DataMole is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# DataMole is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DataMole.  If not, see <https://www.gnu.org/licenses/>.

from typing import List, Optional, Union, Tuple, Set

import numpy as np
import pandas as pd
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Slot, QPointF, Qt, QModelIndex, QMargins
from PySide2.QtGui import QFont, QPainter
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QHBoxLayout, QPushButton, \
    QComboBox, QSplitter, QSizePolicy
from profilehooks import profile

from dataMole.data.types import Types
from dataMole.gui.charts.views import SimpleChartView
from dataMole.gui.mainmodels import SearchableAttributeTableWidget, FrameModel, \
    AttributeTableModel, AttributeProxyModel
from dataMole.gui.panels.dataview import DataView
from dataMole.gui.workbench import WorkbenchModel
from dataMole.utils import safeDelete


class ScatterPlotMatrix(DataView):

    def __init__(self, workbench: WorkbenchModel, parent=None):
        super().__init__(workbench, parent)
        self.__frameModel: FrameModel = None

        # Create widget for the two tables
        sideLayout = QVBoxLayout()
        self.__matrixAttributes = SearchableAttributeTableWidget(self, True, False, False,
                                                                 [Types.Numeric, Types.Ordinal])
        matrixLabel = QLabel('Select at least two numeric attributes and press \'Create chart\' to plot')
        matrixLabel.setWordWrap(True)
        createButton = QPushButton('Create chart', self)
        self.__colorByBox = QComboBox(self)

        sideLayout.addWidget(matrixLabel)
        sideLayout.addWidget(self.__matrixAttributes)
        sideLayout.addWidget(self.__colorByBox, 0, Qt.AlignBottom)
        sideLayout.addWidget(createButton, 0, Qt.AlignBottom)
        self.__matrixLayout: QGridLayout = None
        self.__layout = QHBoxLayout(self)
        self.__comboModel = AttributeProxyModel([Types.String, Types.Ordinal, Types.Nominal], self)

        # Error label to signal errors
        self.errorLabel = QLabel(self)
        self.errorLabel.setWordWrap(True)
        sideLayout.addWidget(self.errorLabel)
        self.errorLabel.hide()

        self.__splitter = QSplitter(self)
        chartWidget = QWidget(self)
        sideWidget = QWidget(self)
        sideWidget.setLayout(sideLayout)
        chartWidget.setMinimumWidth(300)
        self.__splitter.addWidget(chartWidget)
        self.__splitter.addWidget(sideWidget)
        self.__splitter.setSizes([600, 300])
        self.__layout.addWidget(self.__splitter)
        self.__splitter.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
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
    @profile
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
    @profile
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
    @profile
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
        attributes: Set[int] = self.__matrixAttributes.model().checked
        if len(attributes) < 2:
            self.errorLabel.setText('Select at least 2 attributes')
            self.errorLabel.setStyleSheet('color: red')
            self.errorLabel.show()
            return  # stop
        elif self.errorLabel.isVisible():
            self.errorLabel.hide()
        # Get index of groupBy Attribute
        group: int = None
        selectedIndex = self.__colorByBox.currentIndex()
        if self.__comboModel.rowCount() > 0 and selectedIndex != -1:
            index: QModelIndex = self.__comboModel.mapToSource(
                self.__comboModel.index(selectedIndex, 0, QModelIndex()))
            group = index.row() if index.isValid() else None

        # Get attributes of interest
        toKeep: List[int] = list(attributes) if group is None else [group, *attributes]
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
                    view1 = SimpleChartView(plainChart, self)
                    view2 = SimpleChartView(invertedChart, self)
                    view1.setRenderHint(QPainter.Antialiasing)
                    view2.setRenderHint(QPainter.Antialiasing)
                    self.__matrixLayout.addWidget(view1, r, c)
                    self.__matrixLayout.addWidget(view2, c, r)
        self.__matrixLayout.setSpacing(2)

    def clearScatterPlotMatrix(self) -> None:
        # if self.__matrixLayout:
        #     # Delete every child widget
        #     while self.__matrixLayout.count() > 0:
        #         child = self.__matrixLayout.itemAt(0).widget()
        #         if child:
        #             self.__matrixLayout.removeWidget(child)
        #             child.deleteLater()
        #     self.__matrixLayout.deleteLater()
        # Create a new widget for grid layout and add it to the splitter
        chartWidget: QWidget = QWidget(self)
        self.__matrixLayout = QGridLayout(chartWidget)
        self.__splitter.widget(0).hide()
        # Replace layout and delete the previous one
        oldWidget = self.__splitter.replaceWidget(0, chartWidget)
        chartWidget.setMinimumWidth(oldWidget.minimumWidth())
        # Sometimes it's hidden by default
        chartWidget.show()
        # self.__splitter.setSizes([600, 300])
        safeDelete(oldWidget)
        print(chartWidget.size().toTuple())

    @Slot(str, str)
    def onFrameSelectionChanged(self, frameName: str, *_) -> None:
        if not frameName:
            return
        self.__frameModel = self._workbench.getDataframeModelByName(frameName)
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
