import os
from typing import List, Tuple

import numpy as np
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Qt, QPointF, QRectF, QRect, Slot, QSize
from PySide2.QtGui import QFont, QFontMetrics, QPainterPath, QColor, QKeyEvent, QWheelEvent, \
    QKeySequence, QMouseEvent, QCursor, QPixmap, QResizeEvent
from PySide2.QtWidgets import QGraphicsSimpleTextItem, \
    QGraphicsItem, QWidget, QMainWindow, QMenuBar, QAction, QGraphicsView, QApplication, QFileDialog

from data_preprocessor import flogging
from data_preprocessor.gui.charts.utils import copyChart, computeAxisValue


class Callout(QGraphicsItem):
    def __init__(self, chart):
        super().__init__(chart)
        self._chart = chart
        self._text = ""
        self._textRect = QRectF()
        self._anchor = QPointF()
        self._font = QFont()
        self._rect = QRectF()

    def boundingRect(self):
        anchor = self.mapFromParent(self._chart.mapToPosition(self._anchor))
        rect = QRectF()
        rect.setLeft(min(self._rect.left(), anchor.x()))
        rect.setRight(max(self._rect.right(), anchor.x()))
        rect.setTop(min(self._rect.top(), anchor.y()))
        rect.setBottom(max(self._rect.bottom(), anchor.y()))

        return rect

    def paint(self, painter, option, widget):
        path = QPainterPath()
        path.addRoundedRect(self._rect, 5, 5)
        anchor = self.mapFromParent(self._chart.mapToPosition(self._anchor))
        if not self._rect.contains(anchor) and not self._anchor.isNull():
            point1 = QPointF()
            point2 = QPointF()

            # establish the position of the anchor point in relation to _rect
            above = anchor.y() <= self._rect.top()
            aboveCenter = (self._rect.top() < anchor.y() <= self._rect.center().y())
            belowCenter = (self._rect.center().y() < anchor.y() <= self._rect.bottom())
            below = anchor.y() > self._rect.bottom()

            onLeft = anchor.x() <= self._rect.left()
            leftOfCenter = (self._rect.left() < anchor.x() <= self._rect.center().x())
            rightOfCenter = (self._rect.center().x() < anchor.x() <= self._rect.right())
            onRight = anchor.x() > self._rect.right()

            # get the nearest _rect corner.
            x = (onRight + rightOfCenter) * self._rect.width()
            y = (below + belowCenter) * self._rect.height()
            cornerCase = ((above and onLeft) or (above and onRight) or
                          (below and onLeft) or (below and onRight))
            vertical = abs(anchor.x() - x) > abs(anchor.y() - y)

            x1 = (x + leftOfCenter * 10 - rightOfCenter * 20 + cornerCase *
                  int(not vertical) * (onLeft * 10 - onRight * 20))
            y1 = (y + aboveCenter * 10 - belowCenter * 20 + cornerCase *
                  vertical * (above * 10 - below * 20))
            point1.setX(x1)
            point1.setY(y1)

            x2 = (x + leftOfCenter * 20 - rightOfCenter * 10 + cornerCase *
                  int(not vertical) * (onLeft * 20 - onRight * 10))
            y2 = (y + aboveCenter * 20 - belowCenter * 10 + cornerCase *
                  vertical * (above * 20 - below * 10))
            point2.setX(x2)
            point2.setY(y2)

            path.moveTo(point1)
            path.lineTo(anchor)
            path.lineTo(point2)
            path = path.simplified()

        painter.setBrush(QColor(255, 255, 255))
        painter.drawPath(path)
        painter.drawText(self._textRect, self._text)

    def mousePressEvent(self, event):
        event.setAccepted(True)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.setPos(self.mapToParent(event.pos() - event.buttonDownPos(Qt.LeftButton)))
            event.setAccepted(True)
        else:
            event.setAccepted(False)

    def setText(self, text):
        self._text = text
        metrics = QFontMetrics(self._font)
        self._textRect = QRectF(metrics.boundingRect(QRect(0, 0, 150, 150), Qt.AlignLeft, self._text))
        self._textRect.translate(5, 5)
        self.prepareGeometryChange()
        self._rect = self._textRect.adjusted(-5, -5, 5, 5)

    def setAnchor(self, point):
        self._anchor = QPointF(point)

    def updateGeometry(self):
        self.prepareGeometryChange()
        self.setPos(self._chart.mapToPosition(self._anchor) + QPointF(10, -50))

    def __eq__(self, other: 'Callout') -> bool:
        return self._anchor == other._anchor

    def __ne__(self, other: 'Callout') -> bool:
        return not (self == other)


class SimpleChartView(QtCharts.QChartView):
    """ A basic ChartView with no interaction that reacts to double clicks """

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            chartWindow = InteractiveChartWindow(self)  # needs a parent to be kept alive
            # Open widget with plot
            chart = copyChart(self.chart())
            iView = InteractiveChartView(chart=chart, setInWindow=True)
            iView.enableKeySequences(False)
            iView.setRenderHints(self.renderHints())
            chartWindow.setAttribute(Qt.WA_DeleteOnClose, True)
            chartWindow.setCentralWidget(iView)  # window takes ownership of view
            chartWindow.resize(500, 500)
            chartWindow.show()
            event.accept()
        super().mouseDoubleClickEvent(event)


class InteractiveChartView(QtCharts.QChartView):
    """ A ChartView which optionally supports value tooltip, mouse position tracker, zoom and pan """

    def __init__(self, chart: QtCharts.QChart = None, parent: QWidget = None, setInWindow: bool = False):
        super().__init__(parent)
        self._setInWindow: bool = setInWindow
        self._coordX: QGraphicsItem = None
        self._coordY: QGraphicsItem = None
        # self.__callouts: List[Callout] = None # Disabled for now
        self._tooltip: Callout = None
        # Internal fields
        self._mousePressEventPos: QPointF = None
        self._panOn: bool = False
        self._chartIsSet: bool = False  # True iff a valid (i.e. non empty) chart is set in this view
        # Option enable flags
        self._panEnabled: bool = True
        self._zoomEnabled: bool = True
        self._keySeqEnabled: bool = True
        self._calloutEnabled: bool = True
        self._positionTrackerEnabled: bool = True
        self._openInWindowDoubleClick: bool = True

        self.setDragMode(QGraphicsView.NoDrag)
        self.setRubberBand(QtCharts.QChartView.RectangleRubberBand)
        self.setMouseTracking(True)
        self.setInteractive(True)
        if chart:
            self.setChart(chart)

    def enablePan(self, value: bool) -> None:
        self._panEnabled = value

    def enableZoom(self, value: bool) -> None:
        self._zoomEnabled = value
        if value:
            self.setRubberBand(QtCharts.QChartView.RectangleRubberBand)
        else:
            self.setRubberBand(QtCharts.QChartView.NoRubberBand)

    def enableKeySequences(self, value: bool) -> None:
        self._keySeqEnabled = value

    def enableCallout(self, value: bool) -> None:
        self._calloutEnabled = value

    def enablePositionTracker(self, value: bool) -> None:
        self._positionTrackerEnabled = value

    def enableInWindow(self, value: bool) -> None:
        self._openInWindowDoubleClick = value

    def setChart(self, chart: QtCharts.QChart) -> None:
        """ Sets a new chart in the view. Doesn't delete the previous chart """
        # Set New chart
        super().setChart(chart)
        # Update fields
        series: List[QtCharts.QAbstractSeries] = chart.series()
        if not series:
            # Empty chart
            self._chartIsSet = False
        else:
            self._chartIsSet = True

        # self.__callouts = list()
        self._tooltip = Callout(chart)
        chart.setAcceptHoverEvents(True)
        for s in series:
            # s.clicked.connect(self.keepCallout)
            s.hovered.connect(self.tooltip)

        if self._chartIsSet and self._positionTrackerEnabled:
            self._coordX = QGraphicsSimpleTextItem(chart)
            self._coordX.setText("X: ")
            self._coordY = QGraphicsSimpleTextItem(chart)
            self._coordY.setText("Y: ")
            self._updateMouseTrackerPosition()  # Show them in the correct place

    @staticmethod
    def _updateAxisTickCount(chart: QtCharts.QChart, axis: QtCharts.QAbstractAxis,
                             newSize: QSize) -> None:
        """ Given an axis and the size of the view, sets the number of ticks to the best value
        avoiding too many overlapping labels """
        # Get one label as string and the current number of ticks/labels
        label: str
        ticks: int
        if axis.type() == QtCharts.QAbstractAxis.AxisTypeDateTime:
            ticks = axis.tickCount()  # current number of dates shown
            label = axis.min().toString(axis.format())
        elif axis.type() == QtCharts.QAbstractAxis.AxisTypeBarCategory:
            ticks = axis.count()  # number of labels
            label = axis.at(0)
        elif axis.type() == QtCharts.QAbstractAxis.AxisTypeCategory:
            ticks = axis.count()  # number of labels
            label = axis.categoriesLabels()[0]
        else:
            return  # Axis type not supported
        # Decide which dimension is relevant for resizing
        margins = chart.margins()
        # layoutMargins: (left, top, right, bottom)
        layoutMargins: Tuple[float, ...] = chart.layout().getContentsMargins()
        if layoutMargins:
            layoutMargins = tuple([i if i is not None else 0.0 for i in layoutMargins])
        offset: int = 0
        if axis.orientation() == Qt.Horizontal:
            if margins:
                offset += margins.left() + margins.right()
            if layoutMargins:
                offset += layoutMargins[0] + layoutMargins[2]
            # 'length' is the available space for displaying labels, without margins and the space
            # between every label
            length = newSize.width() - offset - (ticks * 10)
        else:
            if margins:
                offset += margins.top() + margins.bottom()
            if layoutMargins:
                offset += layoutMargins[1] + layoutMargins[3]
            length = newSize.height() - offset - (ticks * 10)
        # Compute the optimal width of the label (in pixel)
        metrics = QFontMetrics(axis.labelsFont())
        optimalWidth: int = metrics.horizontalAdvance(label) * 1.9  # not precise, 1.9 is to fix it

        # Deal with every type separately
        if axis.type() == QtCharts.QAbstractAxis.AxisTypeDateTime:
            # Determine optimal number of ticks to avoid much overlapping
            newTicks = int(length / optimalWidth) - 1
            axis.setTickCount(newTicks)
        elif axis.type() == QtCharts.QAbstractAxis.AxisTypeCategory or axis.type() == \
                QtCharts.QAbstractAxis.AxisTypeBarCategory:
            labelSpace: float = length / (ticks * 2)
            if labelSpace < optimalWidth:
                deg = min([90, np.degrees(np.arccos(labelSpace / optimalWidth) * 1.1)])
                axis.setLabelsAngle(deg)
            else:
                axis.setLabelsAngle(0)

    def setBestTickCount(self, newSize: QSize) -> None:
        if self._chartIsSet:
            xAxis = self.chart().axisX()
            yAxis = self.chart().axisY()
            if xAxis:
                self._updateAxisTickCount(self.chart(), xAxis, newSize)
            if yAxis:
                self._updateAxisTickCount(self.chart(), yAxis, newSize)

    def _updateMouseTrackerPosition(self, xOffset: int = 50, yOffset: int = 20) -> None:
        if self._chartIsSet and self._positionTrackerEnabled:
            # Update coordinates tracker position
            self._coordX.setPos(
                self.chart().size().width() / 2 - xOffset,
                self.chart().size().height() - yOffset)
            self._coordY.setPos(
                self.chart().size().width() / 2 + xOffset,
                self.chart().size().height() - yOffset)

    def resizeEvent(self, event: QResizeEvent):
        if self.scene() and self._chartIsSet:
            self.scene().setSceneRect(QRectF(QPointF(0, 0), event.size()))
            self.chart().resize(event.size())
            # Update axis
            self.setBestTickCount(event.size())
            # Update coordinates tracker position (if tracker is active)
            self._updateMouseTrackerPosition()
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._chartIsSet and self._panEnabled and event.button() == Qt.MiddleButton:
            self._mousePressEventPos = event.pos()
            self._panOn = True
            QApplication.setOverrideCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._panEnabled and self._panOn:
            offset = event.pos() - self._mousePressEventPos
            self.chart().scroll(-offset.x(), offset.y())
            self._mousePressEventPos = event.pos()
            event.accept()
        elif self._chartIsSet and self._positionTrackerEnabled:
            metrics = QFontMetrics(self._coordX.font())
            xVal = self.chart().mapToValue(event.pos()).x()
            yVal = self.chart().mapToValue(event.pos()).y()
            # if self.chart().axisX().type() == QtCharts.QAbstractAxis.AxisTypeDateTime:
            xText: str = 'X: {}'.format(computeAxisValue(self.chart().axisX(), xVal))
            yText: str = 'Y: {}'.format(computeAxisValue(self.chart().axisY(), yVal))
            xSize = metrics.width(xText, -1)
            ySize = metrics.width(yText, -1)
            totSize = xSize + ySize
            self._updateMouseTrackerPosition(xOffset=(totSize // 2))
            self._coordX.setText(xText)
            self._coordY.setText(yText)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._panEnabled and self._panOn:
            self._panOn = False
            QApplication.restoreOverrideCursor()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._chartIsSet:
            return
        if event.key() == Qt.Key_Left:
            self.chart().scroll(-10, 0)
        elif event.key() == Qt.Key_Right:
            self.chart().scroll(+10, 0)
        elif event.key() == Qt.Key_Up:
            self.chart().scroll(0, +10)
        elif event.key() == Qt.Key_Down:
            self.chart().scroll(0, -10)
        elif self._keySeqEnabled and event.key() == Qt.Key_R and event.modifiers() & Qt.ControlModifier:
            self.chart().zoomReset()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._chartIsSet and self._zoomEnabled:
            delta: int = event.angleDelta().y()
            factor = pow(1.25, delta / 240.0)
            self.chart().zoom(factor)
            event.accept()

    # @Slot() # Disabled because it causes too many problems
    # def keepCallout(self):
    #     if not self._calloutEnabled:
    #         return
    #     self.__callouts.append(self._tooltip)
    #     self._tooltip = Callout(self.chart())

    # @Slot()  # Disabled because it causes too many problems
    # def clearCallouts(self) -> None:
    #     for c in self.__callouts:
    #         self.scene().removeItem(c)
    #     self.__callouts = list()

    @Slot(QPointF, bool)
    def tooltip(self, point: QPointF, state: bool):
        if not self._calloutEnabled:
            return
        if not self._tooltip:
            self._tooltip = Callout(self.chart())
        if state:
            self._tooltip.setText('X: {} \nY: {} '
                                  .format(computeAxisValue(self.chart().axisX(), point.x()),
                                          computeAxisValue(self.chart().axisY(), point.y())))
            self._tooltip.setAnchor(point)
            self._tooltip.setZValue(11)
            self._tooltip.updateGeometry()
            self._tooltip.show()
        else:
            self._tooltip.hide()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self._chartIsSet and self._openInWindowDoubleClick and not self._setInWindow and \
                event.button() == Qt.LeftButton:
            chartWindow = InteractiveChartWindow(self)  # needs a parent to be kept alive
            # Open widget with plot
            chart = copyChart(self.chart())
            iView = InteractiveChartView(chart=chart, setInWindow=True)
            iView.enableKeySequences(False)
            iView.setRenderHints(self.renderHints())
            chartWindow.setAttribute(Qt.WA_DeleteOnClose, True)
            chartWindow.setCentralWidget(iView)  # window takes ownership of view
            chartWindow.resize(600, 500)
            chartWindow.show()
            event.accept()
        super().mouseDoubleClickEvent(event)


class BarsInteractiveChartView(InteractiveChartView):
    """ Reimplementation of InteractiveChartView specific for bar charts """

    @Slot(bool, int, QtCharts.QBarSet)
    def tooltip(self, status: bool, index: int, barSet: QtCharts.QBarSet) -> None:
        if not self._calloutEnabled:
            return
        if not self._tooltip:
            self._tooltip = Callout(self.chart())
        if status:
            # Compute chart position
            pos = QCursor.pos()
            scenePos = self.mapToScene(self.mapFromGlobal(pos))
            chartPos = self.chart().mapFromScene(scenePos)
            pos = self.chart().mapToValue(chartPos, self.chart().series()[0])
            self._tooltip.setText('N: {:g}'.format((barSet.at(index))))
            self._tooltip.setAnchor(pos)
            self._tooltip.setZValue(11)
            self._tooltip.updateGeometry()
            self._tooltip.show()
        else:
            self._tooltip.hide()


class InteractiveChartWindow(QMainWindow):
    """ Window with an interactive chart view with panning, zoom, menu bar """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view: QtCharts.QChartView = None
        menuBar = QMenuBar()
        fileMenu = menuBar.addMenu('File')
        self._saveAc = QAction('Save as image', fileMenu)
        self._saveAc.setShortcut(QKeySequence(self.tr('Ctrl+S')))
        self._closeAc = QAction('Close', fileMenu)
        viewMenu = menuBar.addMenu('View')
        self._resetAc = QAction('Reset zoom', viewMenu)
        self._resetAc.setShortcut(QKeySequence(self.tr('Ctrl+R')))
        self._zoomInAc = QAction('Zoom in', viewMenu)
        self._zoomInAc.setShortcut(QKeySequence(self.tr('Ctrl++')))
        self._zoomOutAc = QAction('Zoom out', viewMenu)
        self._zoomOutAc.setShortcut(QKeySequence(self.tr('Ctrl+-')))
        fileMenu.addActions([self._saveAc, self._closeAc])
        viewMenu.addActions([self._zoomInAc, self._zoomOutAc, self._resetAc])
        self.setMenuBar(menuBar)
        self.setWindowTitle('dataMole - Plot')

    def setCentralWidget(self, widget: InteractiveChartView) -> None:
        super().setCentralWidget(widget)
        self.view = widget

        self._zoomInAc.triggered.connect(self.zoomIn)
        self._zoomOutAc.triggered.connect(self.zoomOut)
        self._resetAc.triggered.connect(self.zoomReset)
        self._closeAc.triggered.connect(self.close)
        # self._clearCalloutsAc.triggered.connect(self.view.clearCallouts)
        self._saveAc.triggered.connect(self.saveImage)

    @Slot()
    def zoomIn(self) -> None:
        self.view.chart().zoomIn()

    @Slot()
    def zoomOut(self) -> None:
        self.view.chart().zoomOut()

    @Slot()
    def zoomReset(self) -> None:
        self.view.chart().zoomReset()

    @Slot()
    def saveImage(self) -> None:
        filename = QFileDialog \
            .getSaveFileName(self,
                             caption=self.tr('Save chart as image'),
                             dir=os.getcwd(),
                             filter=self.tr('png (*.png);;jpeg (*.jpg);;xpm (*.xpm);;bmp (*.bmp)'))
        p: QPixmap = self.view.grab()
        name, ext = filename
        f: str = name.strip() + '.' + ext.strip().split(' ')[0]
        saved: bool = p.save(f)
        flogging.appLogger.info('Image saved: {}'.format(saved))
