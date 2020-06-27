import logging
import os
from typing import List

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Qt, QPointF, QRectF, QRect, Slot, QSize
from PySide2.QtGui import QPainter, QFont, QFontMetrics, QPainterPath, QColor, QKeyEvent, QWheelEvent, \
    QKeySequence, QMouseEvent, QCursor, QPixmap, QResizeEvent
from PySide2.QtWidgets import QGraphicsSimpleTextItem, \
    QGraphicsItem, QWidget, QMainWindow, QMenuBar, QAction, QGraphicsView, QApplication, QFileDialog

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
            chartWindow.setAttribute(Qt.WA_DeleteOnClose, True)
            chartWindow.setCentralWidget(iView)  # window takes ownership of view
            chartWindow.resize(500, 500)
            chartWindow.show()
            event.accept()
        super().mouseDoubleClickEvent(event)


class InteractiveChartView(QtCharts.QChartView):
    def __init__(self, chart: QtCharts.QChart = None, parent: QWidget = None, setInWindow: bool = False):
        super().__init__(parent)
        self.__setInWindow: bool = setInWindow
        self.__coordX: QGraphicsItem = None
        self.__coordY: QGraphicsItem = None
        self.__callouts: List[Callout] = None
        self.__tooltip: Callout = None
        # Wheel drag
        self.__mousePressEventPos: QPointF = None
        self.__panOn: bool = False
        self.__chartIsSet: bool = False
        # Option enable flags
        self.__panEnabled: bool = True
        self.__zoomEnabled: bool = True
        self.__keySeqEnabled: bool = True

        self.setDragMode(QGraphicsView.NoDrag)
        self.setRubberBand(QtCharts.QChartView.RectangleRubberBand)
        self.setMouseTracking(True)
        self.setInteractive(True)
        if chart:
            self.setChart(chart)

    def enablePan(self, value: bool) -> None:
        self.__panEnabled = value

    def enableZoom(self, value: bool) -> None:
        self.__zoomEnabled = value
        if value:
            self.setRubberBand(QtCharts.QChartView.RectangleRubberBand)
        else:
            self.setRubberBand(QtCharts.QChartView.NoRubberBand)

    def enableKeySequences(self, value: bool) -> None:
        self.__keySeqEnabled = value

    def setChart(self, chart: QtCharts.QChart) -> None:
        # Save old chart to delete it at the end
        oldChart = self.chart()
        # New chart
        self.__callouts = list()
        self.__tooltip = Callout(chart)
        series: List[QtCharts.QAbstractSeries] = chart.series()
        chart.legend().show()
        chart.setAcceptHoverEvents(True)
        for s in series:
            s.clicked.connect(self.keepCallout)
            s.hovered.connect(self.tooltip)

        self.setRenderHint(QPainter.Antialiasing)
        # self.scene().addItem(self.__chart)

        self.__coordX = QGraphicsSimpleTextItem(chart)
        # self.__coordX.setPos(self.__chart.size().width() / 2 - 50, self.__chart.size().height())
        self.__coordX.setText("X: ")
        self.__coordY = QGraphicsSimpleTextItem(chart)
        # self.__coordY.setPos(self.__chart.size().width() / 2 + 50, self.__chart.size().height())
        self.__coordY.setText("Y: ")

        super().setChart(chart)
        if oldChart:
            oldChart.deleteLater()
        self.__chartIsSet = True

    @staticmethod
    def _updateAxisTickCount(axis: QtCharts.QAbstractAxis, newSize: QSize) -> None:
        """ Given an axis and the size of the view, sets the number of ticks to the best value
        avoiding too many overlapping labels """
        if axis.type() == QtCharts.QAbstractAxis.AxisTypeCategory or axis.type() == \
                QtCharts.QAbstractAxis.AxisTypeDateTime:
            ticks = axis.tickCount()
            # Decide which dimension is relevant
            if axis.orientation() == Qt.Horizontal:
                length = newSize.width()
            else:
                length = newSize.height()
            # Get one label as string
            label: str
            if axis.type() == QtCharts.QAbstractAxis.AxisTypeCategory:
                label = axis.categoriesLabels()[0]
            else:
                label = axis.min().toString(axis.format())
            # Compute the optimal width of the label (in pixel)
            metrics = QFontMetrics(axis.labelsFont())
            optimalWidth: int = metrics.width(label)
            optimalWidth += optimalWidth * 0.30
            # Determine optimal number of ticks to avoid much overlapping
            newTicks = int(length / optimalWidth) - 1
            axis.setTickCount(newTicks)

            # TODO: test if this works with categories, otherwise remove it
            if axis.type() == QtCharts.QAbstractAxis.AxisTypeCategory:
                allTicks = ticks + axis.minorTickCount()
                newMinorTicks = int((allTicks - newTicks) / newTicks)
                axis.setMinorTickCount(newMinorTicks)

    def setBestTickCount(self, newSize: QSize) -> None:
        if self.__chartIsSet:
            xAxis = self.chart().axisX()
            yAxis = self.chart().axisY()
            if xAxis:
                InteractiveChartView._updateAxisTickCount(xAxis, newSize)
            if yAxis:
                InteractiveChartView._updateAxisTickCount(yAxis, newSize)

    def resizeEvent(self, event: QResizeEvent):
        if self.scene() and self.__chartIsSet:
            self.scene().setSceneRect(QRectF(QPointF(0, 0), event.size()))
            self.chart().resize(event.size())
            # Update axis
            self.setBestTickCount(event.size())
            # Update callouts position
            self.__coordX.setPos(
                self.chart().size().width() / 2 - 50,
                self.chart().size().height() - 20)
            self.__coordY.setPos(
                self.chart().size().width() / 2 + 50,
                self.chart().size().height() - 20)
            for callout in self.__callouts:
                callout.updateGeometry()
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.__panEnabled and event.button() == Qt.MiddleButton:
            self.__mousePressEventPos = event.pos()
            self.__panOn = True
            QApplication.setOverrideCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.__panEnabled and self.__panOn:
            offset = event.pos() - self.__mousePressEventPos
            self.chart().scroll(-offset.x(), offset.y())
            self.__mousePressEventPos = event.pos()
            event.accept()
        elif self.__chartIsSet:
            metrics = QFontMetrics(self.__coordX.font())
            xVal = self.chart().mapToValue(event.pos()).x()
            yVal = self.chart().mapToValue(event.pos()).y()
            # if self.chart().axisX().type() == QtCharts.QAbstractAxis.AxisTypeDateTime:
            xText: str = 'X: {}'.format(computeAxisValue(self.chart().axisX(), xVal))
            yText: str = 'Y: {}'.format(computeAxisValue(self.chart().axisY(), yVal))
            xSize = metrics.width(xText, -1)
            ySize = metrics.width(yText, -1)
            totSize = xSize + ySize
            self.__coordX.setPos(
                self.chart().size().width() / 2 - (totSize / 2),
                self.chart().size().height() - 20)
            self.__coordY.setPos(
                self.chart().size().width() / 2 + (totSize / 2),
                self.chart().size().height() - 20)
            self.__coordX.setText(xText)
            self.__coordY.setText(yText)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.__panEnabled and self.__panOn:
            self.__panOn = False
            QApplication.restoreOverrideCursor()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Left:
            self.chart().scroll(-10, 0)
        elif event.key() == Qt.Key_Right:
            self.chart().scroll(+10, 0)
        elif event.key() == Qt.Key_Up:
            self.chart().scroll(0, +10)
        elif event.key() == Qt.Key_Down:
            self.chart().scroll(0, -10)
        elif self.__keySeqEnabled and event.key() == Qt.Key_R and event.modifiers() & Qt.ControlModifier:
            self.chart().zoomReset()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.__zoomEnabled:
            delta: int = event.angleDelta().y()
            factor = pow(1.25, delta / 240.0)
            self.chart().zoom(factor)
            event.accept()

    @Slot()
    def keepCallout(self):
        self.__callouts.append(self.__tooltip)
        self.__tooltip = Callout(self.chart())

    @Slot(QPointF, bool)
    def tooltip(self, point: QPointF, state: bool):
        if not self.__tooltip:
            self.__tooltip = Callout(self.chart())
        if state:
            self.__tooltip.setText('X: {} \nY: {} '
                                   .format(computeAxisValue(self.chart().axisX(), point.x()),
                                           computeAxisValue(self.chart().axisY(), point.y())))
            self.__tooltip.setAnchor(point)
            self.__tooltip.setZValue(11)
            self.__tooltip.updateGeometry()
            self.__tooltip.show()
        else:
            self.__tooltip.hide()

    @Slot()
    def clearCallouts(self) -> None:
        for c in self.__callouts:
            self.scene().removeItem(c)
        self.__callouts = list()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if not self.__setInWindow and event.button() == Qt.LeftButton:
            chartWindow = InteractiveChartWindow(self)  # needs a parent to be kept alive
            # Open widget with plot
            chart = copyChart(self.chart())
            iView = InteractiveChartView(chart=chart, setInWindow=True)
            iView.enableKeySequences(False)
            chartWindow.setAttribute(Qt.WA_DeleteOnClose, True)
            chartWindow.setCentralWidget(iView)  # window takes ownership of view
            chartWindow.resize(600, 500)
            chartWindow.show()
            event.accept()
        super().mouseDoubleClickEvent(event)


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
        self._clearCalloutsAc = QAction('Clear tooltips', viewMenu)
        self._clearCalloutsAc.setShortcut(QKeySequence(self.tr('Ctrl+T')))
        fileMenu.addActions([self._saveAc, self._closeAc])
        viewMenu.addActions([self._zoomInAc, self._zoomOutAc, self._resetAc, self._clearCalloutsAc])
        self.setMenuBar(menuBar)

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
        logging.info('Image saved: {}'.format(saved))
