import logging
import os
from typing import List

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Qt, QPointF, QRectF, QRect, Slot
from PySide2.QtGui import QPainter, QFont, QFontMetrics, QPainterPath, QColor, QKeyEvent, QWheelEvent, \
    QKeySequence, QMouseEvent, QCursor, QPixmap
from PySide2.QtWidgets import QGraphicsSimpleTextItem, \
    QGraphicsItem, QWidget, QMainWindow, QMenuBar, QAction, QGraphicsView, QApplication, QFileDialog


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
            iView = InteractiveChartView(chart=self.chart(), topLevel=True)
            chartWindow.setAttribute(Qt.WA_DeleteOnClose, True)
            chartWindow.setCentralWidget(iView)  # window takes ownership of view
            chartWindow.resize(500, 500)
            chartWindow.show()
            event.accept()
        super().mouseDoubleClickEvent(event)


class InteractiveChartView(QtCharts.QChartView):
    def __init__(self, chart: QtCharts.QChart = None, parent: QWidget = None, topLevel: bool = False):
        super().__init__(parent)
        self.__isTopLevel: bool = topLevel
        self.__coordX: QGraphicsItem = None
        self.__coordY: QGraphicsItem = None
        self.__callouts: List[Callout] = None
        self.__tooltip: Callout = None
        # Wheel drag
        self.__mousePressEventPos: QPointF = None
        self.__panOn: bool = False

        self.setDragMode(QGraphicsView.NoDrag)
        self.setRubberBand(QtCharts.QChartView.RectangleRubberBand)
        self.setMouseTracking(True)
        self.setInteractive(True)
        if chart:
            self.setChart(chart)

    def setChart(self, chart: QtCharts.QChart) -> None:
        # Save old chart to delete it at the end
        oldChart = self.chart()
        # New chart
        chart_c = QtCharts.QChart()
        self.__callouts = list()
        self.__tooltip = Callout(chart_c)
        series: List[QtCharts.QAbstractSeries] = chart.series()
        for s in series:
            # Create new series with same points
            s_copy = QtCharts.QScatterSeries()
            # s_copy.setUseOpenGL(True)
            s_copy.append(s.points())
            s_copy.setName(s.name())
            # Add series to chart
            chart_c.addSeries(s_copy)
            s_copy.clicked.connect(self.keepCallout)
            s_copy.hovered.connect(self.tooltip)
        # self._chart.setMinimumSize(640, 480)
        chart_c.legend().show()
        chart_c.createDefaultAxes()
        chart_c.axisX().setTitleText(chart.axisX().titleText())
        chart_c.axisY().setTitleText(chart.axisY().titleText())
        chart_c.setAcceptHoverEvents(True)

        self.setRenderHint(QPainter.Antialiasing)
        # self.scene().addItem(self.__chart)

        self.__coordX = QGraphicsSimpleTextItem(chart_c)
        # self.__coordX.setPos(self.__chart.size().width() / 2 - 50, self.__chart.size().height())
        self.__coordX.setText("X: ")
        self.__coordY = QGraphicsSimpleTextItem(chart_c)
        # self.__coordY.setPos(self.__chart.size().width() / 2 + 50, self.__chart.size().height())
        self.__coordY.setText("Y: ")

        super().setChart(chart_c)
        if oldChart:
            oldChart.deleteLater()

    def resizeEvent(self, event):
        if self.scene():
            self.scene().setSceneRect(QRectF(QPointF(0, 0), event.size()))
            self.chart().resize(event.size())
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
        if event.button() == Qt.MiddleButton:
            self.__mousePressEventPos = event.pos()
            self.__panOn = True
            QApplication.setOverrideCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.__panOn:
            offset = event.pos() - self.__mousePressEventPos
            self.chart().scroll(-offset.x(), offset.y())
            self.__mousePressEventPos = event.pos()
            event.accept()
        else:
            self.__coordX.setText("X: {0:.2f}"
                                  .format(self.chart().mapToValue(event.pos()).x()))
            self.__coordY.setText("Y: {0:.2f}"
                                  .format(self.chart().mapToValue(event.pos()).y()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.__panOn:
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
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
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
            self.__tooltip.setText('X: {0:.2f} \nY: {1:.2f} '.format(point.x(), point.y()))
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
        if not self.__isTopLevel and event.button() == Qt.LeftButton:
            chartWindow = InteractiveChartWindow(self)  # needs a parent to be kept alive
            # Open widget with plot
            iView = InteractiveChartView(chart=self.chart(), topLevel=True)
            chartWindow.setAttribute(Qt.WA_DeleteOnClose, True)
            chartWindow.setCentralWidget(iView)  # window takes ownership of view
            chartWindow.resize(500, 500)
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
