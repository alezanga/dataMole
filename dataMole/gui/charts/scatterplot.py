# -*- coding: utf-8 -*-
#
# Author:       Alessandro Zangari (alessandro.zangari.code@outlook.com)
# Copyright:    © Copyright 2020 Alessandro Zangari, Università degli Studi di Padova
# License:      GPL-3.0-or-later
# Date:         2020-10-04
# Version:      1.1
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

from typing import List, Optional, Union, Set, Tuple, Any

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide2.QtCore import Slot, Qt, QModelIndex, QThreadPool, QObject, Signal
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, \
    QComboBox, QSplitter, QSizePolicy, QApplication, QCheckBox

from dataMole.data.types import Types
from dataMole.gui.charts.utils import randomColors
from dataMole.gui.charts.views import GraphicsPlotLayout
from dataMole.gui.mainmodels import SearchableAttributeTableWidget, FrameModel, \
    AttributeTableModel, AttributeProxyModel
from dataMole.gui.panels.dataview import DataView
from dataMole.gui.widgets.waitingspinnerwidget import QtWaitingSpinner
from dataMole.gui.workbench import WorkbenchModel
from dataMole.threads import Worker
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
        self.__createButton = QPushButton('Create chart', self)
        self.__colorByBox = QComboBox(self)
        self.__autoDownsample = QCheckBox('Auto downsample', self)
        self.__useOpenGL = QCheckBox('Use OpenGL', self)
        self.__autoDownsample.setToolTip('If too many points are to be rendered, this will try\n'
                                         'to plot only a subsample, improving performance with\n'
                                         'zooming and panning, but increasing rendering time')
        self.__useOpenGL.setToolTip('Enforce usage of GPU acceleration to render charts.\n'
                                    'It is still an experimental feature but should speed\n'
                                    'up rendering with huge set of points')

        # Layout for checkboxes
        optionsLayout = QHBoxLayout()
        optionsLayout.addWidget(self.__autoDownsample, 0, Qt.AlignRight)
        optionsLayout.addWidget(self.__useOpenGL, 0, Qt.AlignRight)

        sideLayout.addWidget(matrixLabel)
        sideLayout.addWidget(self.__matrixAttributes)
        sideLayout.addLayout(optionsLayout)
        sideLayout.addWidget(self.__colorByBox, 0, Qt.AlignBottom)
        sideLayout.addWidget(self.__createButton, 0, Qt.AlignBottom)
        self.__matrixLayout: pg.GraphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.__layout = QHBoxLayout(self)
        self.__comboModel = AttributeProxyModel([Types.String, Types.Ordinal, Types.Nominal], self)

        # Error label to signal errors
        self.errorLabel = QLabel(self)
        self.errorLabel.setWordWrap(True)
        sideLayout.addWidget(self.errorLabel)
        self.errorLabel.hide()

        self.__splitter = QSplitter(self)
        sideWidget = QWidget(self)
        sideWidget.setLayout(sideLayout)
        # chartWidget.setMinimumWidth(300)
        self.__splitter.addWidget(self.__matrixLayout)
        self.__splitter.addWidget(sideWidget)
        self.__splitter.setSizes([600, 300])
        self.__layout.addWidget(self.__splitter)
        self.__splitter.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # Connect
        self.__createButton.clicked.connect(self.showScatterPlots)

        self.spinner = QtWaitingSpinner(self.__matrixLayout)

    @Slot()
    def showScatterPlots(self) -> None:
        self.__createButton.setDisabled(True)
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

        # Create a new matrix layout and delete the old one
        matrix = GraphicsPlotLayout(parent=self)
        self.spinner = QtWaitingSpinner(matrix)
        oldM = self.__splitter.replaceWidget(0, matrix)
        self.__matrixLayout = matrix
        safeDelete(oldM)
        matrix.useOpenGL(self.__useOpenGL.isChecked())
        matrix.show()

        # Get attributes of interest
        toKeep: List[int] = list(attributes) if group is None else [group, *attributes]
        filterDf = self.__frameModel.frame.getRawFrame().iloc[:, toKeep]
        # Create a worker to create scatter-plots on different thread
        worker = Worker(ProcessDataframe(), (filterDf, group, attributes))

        worker.signals.result.connect(self.__createPlots)
        # No need to deal with error/finished signals since there is nothing to do
        worker.setAutoDelete(True)
        self.spinner.start()
        QThreadPool.globalInstance().start(worker)

    def resetScatterPlotMatrix(self) -> None:
        # Create a new matrix layout
        matrix = pg.GraphicsLayoutWidget(parent=self)
        self.spinner = QtWaitingSpinner(matrix)
        oldM = self.__splitter.replaceWidget(0, matrix)
        self.__matrixLayout = matrix
        safeDelete(oldM)
        matrix.show()

    @Slot(object, object)
    def __createPlots(self, _, result: Tuple[pd.DataFrame, List[str], List[int], bool]) -> None:
        """ Create plots and render all graphic items """
        # Unpack results
        df, names, attributes, grouped = result

        # Populate the matrix
        for r in range(len(attributes)):
            for c in range(len(attributes)):
                if r == c:
                    name: str = names[r]
                    self.__matrixLayout.addLabel(row=r, col=c, text=name)
                else:
                    xColName: str = names[c]
                    yColName: str = names[r]
                    seriesList = self.__createScatterSeries(df=df, xCol=xColName, yCol=yColName, groupBy=grouped,
                                                            ds=self.__autoDownsample.isChecked())
                    plot = self.__matrixLayout.addPlot(row=r, col=c)
                    for series in seriesList:
                        plot.addItem(series)
                    # Coordinates and data for later use
                    plot.row = r
                    plot.col = c
                    plot.xName = xColName
                    plot.yName = yColName
        # When all plot are created stop spinner and re-enable button
        self.spinner.stop()
        self.__createButton.setEnabled(True)

    @staticmethod
    def __createScatterSeries(df: Union[pd.DataFrame, pd.core.groupby.DataFrameGroupBy], xCol: str,
                              yCol: str, groupBy: bool, ds: bool) -> List[pg.PlotDataItem]:
        """
        Creates a list of series of points to be plotted in the scatterplot

        :param df: the input dataframe
        :param xCol: name of the feature to use as x-axis
        :param yCol: name of the feature to use as y-axis
        :param groupBy: whether the feature dataframe is grouped by some attribute
        :param ds: whether to auto downsample the set of points during rendering

        :return:

        """
        allSeries = list()
        if groupBy:
            df: pd.core.groupby.DataFrameGroupBy
            colours = randomColors(len(df))
            i = 0
            for groupName, groupedDf in df:
                # Remove any row with nan values
                gdf = groupedDf.dropna()
                qSeries1 = pg.PlotDataItem(x=gdf[xCol], y=gdf[yCol], autoDownsample=ds,
                                           name=str(groupName), symbolBrush=pg.mkBrush(colours[i]),
                                           symbol='o', pen=None)
                allSeries.append(qSeries1)
                i += 1
        else:
            df: pd.DataFrame
            # Remove any row with nan values
            df = df.dropna()
            series = pg.PlotDataItem(x=df[xCol], y=df[yCol], autoDownsample=ds, symbol='o', pen=None)
            allSeries.append(series)
        return allSeries

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
        self.resetScatterPlotMatrix()


class ProcessDataframe:
    def execute(self, filterDf: pd.DataFrame, group: int, attributes: List[int]) -> \
            Tuple[pd.DataFrame, List[str], List[int], bool]:
        """ Preprocess a dataframe for visualisation doing groupby operations if required """
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

        return df, attributesColumnNames, attributes, bool(groupName)

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
