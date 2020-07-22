import math
from typing import List, Optional

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QDateTime
from PySide2.QtGui import QColor

from data_preprocessor import flogging


def randomColors(count: int) -> List[QColor]:
    colors = list()
    current: float = 0.0
    for i in range(0, count):
        colors.append(QColor.fromHslF(current, 1.0, 0.5))
        current += 0.618033988749895
        current = math.fmod(current, 1.0)
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
