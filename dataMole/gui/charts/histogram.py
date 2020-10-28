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

from typing import Dict, Any

from PySide2.QtCharts import QtCharts
from PySide2.QtGui import QFont, Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel, QGraphicsSimpleTextItem

from dataMole.gui.widgets.waitingspinnerwidget import QtWaitingSpinner
from .views import BarsInteractiveChartView
from ...operation.utils import isFloat


class Histogram(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.spinner = QtWaitingSpinner(parent=self, centerOnParent=True,
                                        disableParentWhenSpinning=True)
        self.layout = QVBoxLayout()
        self.chartView = BarsInteractiveChartView(parent=self)
        self.chartView.enablePan(False)
        self.chartView.enableKeySequences(False)
        self.chartView.enableZoom(False)
        self.chartView.enableCallout(True)  # Callout doesn't work
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
                if len(labels) > 1:
                    # If there is one or less labels stop
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
        axisY.setLabelFormat('%d')
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        chart.legend().setVisible(False)

        self.chart = chart
        self.chartView.setChart(self.chart)
