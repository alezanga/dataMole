from PySide2.QtCore import Qt
from PySide2.QtWidgets import QHeaderView


class IndexHeaderView(QHeaderView):
    HorizontalHeaderDataRole = Qt.UserRole
    VerticalHeaderDataRole = Qt.UserRole + 1

    # def paintVerticalSection(self, painter: QPainter, data: Iterable) -> None:
    #     opt = QStyleOptionHeader()
    #     self.initStyleOption(opt)
    #     for d in data:
    #         rect = self.fontMetrics().boundingRect(d)
    #         painter.drawText(rect, d)
    #         painter.drawLine(rect.)

    # def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
    #     painter.save()
    #     super(HierarchicalHeaderView, self).paintSection(painter, rect, logicalIndex)
    #     painter.restore()
    #     if rect.isValid():
    #         data = self.model().headerData(logicalIndex, self.orientation())
    #         if hasattr(data, '__len__'):
    #             if self.orientation() == Qt.Horizontal:
    #                 self.paintVeticalSection(data)
    #             else:
    #                 self.paintHorizontalSection(data)
