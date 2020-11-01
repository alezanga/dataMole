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

import math
from typing import List, Optional

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QDateTime
from PySide2.QtGui import QColor

from dataMole import flogging
import random


def randomColors(count: int) -> List[QColor]:
    colors = list()
    hue: int = random.randint(0, 359)
    for i in range(0, count):
        colors.append(QColor.fromHsl(hue, 255, 127))
        hue += random.randint(360 // (count * 2), 360 // count)
        hue = int(math.fmod(hue, 360))
    return colors


def computeAxisValue(axis: Optional[QtCharts.QAbstractAxis], value: float) -> str:
    """ Provide the label to be visualized at coordinate 'value' of the specified axis """
    if not axis:
        return '-'
    if axis.type() == QtCharts.QAbstractAxis.AxisTypeDateTime:
        axis: QtCharts.QDateTimeAxis
        try:
            qDate = QDateTime.fromMSecsSinceEpoch(int(value))
        except OverflowError as e:
            flogging.appLogger.warning('Axis value error: {}'.format(str(e)))
            text = '-'
        else:
            text = qDate.toString(axis.format())
    elif axis.type() == QtCharts.QAbstractAxis.AxisTypeBarCategory:
        axis: QtCharts.QBarCategoryAxis
        categories = axis.categories()
        if 0 <= round(value) < len(categories):
            text = axis.at(round(value))
        else:
            text = '-'
    elif axis.type() == QtCharts.QAbstractAxis.AxisTypeCategory:
        axis: QtCharts.QCategoryAxis
        categories = axis.categoriesLabels()
        if 0 <= round(value) < len(categories):
            text = axis.categoriesLabels()[round(value)]
        else:
            text = '-'
    else:
        text = '{0:.2f}'.format(value)
    return text


def copyAxis(chart: QtCharts.QChart, axis: QtCharts.QAbstractAxis) -> QtCharts.QAbstractAxis:
    a_copy: QtCharts.QAbstractAxis
    if axis.type() == QtCharts.QAbstractAxis.AxisTypeBarCategory:
        a_copy = QtCharts.QBarCategoryAxis(chart)
        labels = axis.categories()
        a_copy.append(labels)
    elif axis.type() == QtCharts.QAbstractAxis.AxisTypeCategory:
        a_copy = QtCharts.QCategoryAxis(chart)
        labels = axis.categoriesLabels()
        a_copy.setStartValue(axis.startValue(labels[0]))
        a_copy.setLabelsPosition(axis.labelsPosition())
        for lab in labels:
            a_copy.append(lab, axis.endValue(lab))
    elif axis.type() == QtCharts.QAbstractAxis.AxisTypeValue:
        a_copy = QtCharts.QValueAxis(chart)
        a_copy.setMin(axis.min())
        a_copy.setMax(axis.max())
        a_copy.setTickCount(axis.tickCount())
        a_copy.setMinorTickCount(axis.minorTickCount())
        a_copy.setTickInterval(axis.tickInterval())
    elif axis.type() == QtCharts.QAbstractAxis.AxisTypeDateTime:
        a_copy = QtCharts.QDateTimeAxis(chart)
        a_copy.setMin(axis.min())
        a_copy.setMax(axis.max())
        a_copy.setFormat(axis.format())
        a_copy.setTickCount(axis.tickCount())
    else:
        raise NotImplementedError('Cannot copy axis of type {}'.format(str(axis.type())))
    a_copy.setTitleText(axis.titleText())
    a_copy.setTitleFont(axis.titleFont())
    return a_copy


def copyChart(chart: QtCharts.QChart) -> QtCharts.QChart:
    """ Return a copy of the chart """
    newChart = QtCharts.QChart()
    # Copy axes
    axes = chart.axes()
    for axis in axes:
        newChart.addAxis(copyAxis(newChart, axis), axis.alignment())
    # Copy series
    allSeries: List[QtCharts.QAbstractSeries] = chart.series()
    for s in allSeries:
        # Create new series with same points, dependent on actual type
        s_copy: QtCharts.QAbstractSeries
        if isinstance(s, QtCharts.QScatterSeries):
            s_copy = QtCharts.QScatterSeries()
            s_copy.append(s.points())
        elif isinstance(s, QtCharts.QLineSeries):
            s_copy = QtCharts.QLineSeries()
            s_copy.append(s.points())
        elif isinstance(s, QtCharts.QAbstractBarSeries):
            # Note: this is not used
            s_copy = QtCharts.QBarSeries()
            for bar in s.barSets():
                bar_copy = QtCharts.QBarSet(bar.label())
                s_copy.append(bar_copy)
        else:
            raise NotImplementedError('Cannot copy series of type {}'.format(type(s)))
        s_copy.setName(s.name())
        # Add series to chart
        newChart.addSeries(s_copy)
        # Add axis to series
        s_copy.attachAxis(newChart.axisX())
        s_copy.attachAxis(newChart.axisY())
    if chart.title():
        newChart.setTitle(chart.title())
    return newChart
