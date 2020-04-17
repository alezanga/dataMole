from enum import Enum
from typing import List

from PySide2.QtCore import QMargins, Qt, QSize, QRect
from PySide2.QtWidgets import QWidget, QLayout, QLayoutItem, QWidgetItem


# Source: https://doc.qt.io/qt-5/qtwidgets-layouts-borderlayout-example.html


class BorderLayout(QLayout):
    Position = Enum('Position', 'West North South East Center')
    West = Position.West
    North = Position.North
    South = Position.South
    East = Position.East
    Center = Position.Center

    SizeType = Enum('SizeType', 'MinimumSize SizeHint')

    def __init__(self, parent: QWidget = None, margins: QMargins = QMargins(), spacing: int = -1):
        super().__init__(parent)
        if margins != QMargins():
            self.setContentMargins(margins)
        self.setSpacing(spacing)
        self.__list: List[ItemWrapper] = list()

    def add(self, item: QLayoutItem, position: Position) -> None:
        self.__list.append(ItemWrapper(item, position))

    def addItem(self, item: QLayoutItem) -> None:
        self.add(item, BorderLayout.West)

    def addWidget(self, w: QWidget, position: Position) -> None:
        self.add(QWidgetItem(w), position)

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Horizontal | Qt.Vertical

    def hasHeightForWidth(self) -> bool:
        return False

    def count(self) -> int:
        return len(self.__list)

    def itemAt(self, index: int) -> QLayoutItem:
        w: ItemWrapper = self.__list[index]
        return w.item if w.item else None

    def minimumSize(self) -> QSize:
        return self.__calculateSize(BorderLayout.SizeType.MinimumSize)

    def takeAt(self, index: int) -> QLayoutItem:
        if 0 <= index < len(self.__list):
            w: ItemWrapper = self.__list.pop(index)
            return w.item
        return None

    def sizeHint(self) -> QSize:
        return self.__calculateSize(BorderLayout.SizeType.SizeHint)

    def setGeometry(self, rect: QRect) -> None:
        center: ItemWrapper = None
        eastWidth: int = 0
        westWidth: int = 0
        northHeight: int = 0
        southHeight: int = 0
        centerHeight: int = 0
        i: int

        super().setGeometry(rect)
        for wrapper in self.__list:
            item: QLayoutItem = wrapper.item
            position: BorderLayout.Position = wrapper.position

            if position == BorderLayout.North:
                item.setGeometry(QRect(rect.x(), northHeight, rect.width(),
                                       item.sizeHint().height()))

                northHeight += item.geometry().height() + self.spacing()
            elif position == BorderLayout.South:
                item.setGeometry(QRect(item.geometry().x(), item.geometry().y(), rect.width(),
                                       item.sizeHint().height()))

                southHeight += item.geometry().height() + self.spacing()

                item.setGeometry(QRect(rect.x(),
                                       rect.y() + rect.height() - southHeight + self.spacing(),
                                       item.geometry().width(),
                                       item.geometry().height()))
            elif position == BorderLayout.Center:
                center = wrapper

        centerHeight = rect.height() - northHeight - southHeight

        for wrapper in self.__list:
            item: QLayoutItem = wrapper.item
            position: BorderLayout.Position = wrapper.position

            if position == BorderLayout.West:
                item.setGeometry(QRect(rect.x() + westWidth, northHeight,
                                       item.sizeHint().width(), centerHeight))

                westWidth += item.geometry().width() + self.spacing()
            elif position == BorderLayout.East:
                item.setGeometry(QRect(item.geometry().x(), item.geometry().y(),
                                       item.sizeHint().width(), centerHeight))

                eastWidth += item.geometry().width() + self.spacing()

                item.setGeometry(QRect(
                    rect.x() + rect.width() - eastWidth + self.spacing(),
                    northHeight, item.geometry().width(),
                    item.geometry().height()))

        if center:
            center.item.setGeometry(QRect(westWidth, northHeight,
                                          rect.width() - eastWidth - westWidth,
                                          centerHeight))

    def __calculateSize(self, sizeType: SizeType) -> QSize:
        totalSize: QSize = QSize()

        for wrapper in self.__list:
            position: BorderLayout.Position = wrapper.position
            itemSize: QSize

            if sizeType == BorderLayout.SizeType.MinimumSize:
                itemSize = wrapper.item.minimumSize()
            else:  # sizeType == SizeHint
                itemSize = wrapper.item.sizeHint()

            if position == BorderLayout.North or position == BorderLayout.South or position == \
                    BorderLayout.Center:
                h = totalSize.height()
                itemSize.setHeight(h + h)

            if position == BorderLayout.West or position == BorderLayout.East or position == \
                    BorderLayout.Center:
                w = totalSize.width()
                itemSize.setWidth(w + w)

        return totalSize


class ItemWrapper:
    def __init__(self, item: QLayoutItem, position: BorderLayout.Position):
        self.item = item
        self.position = position
