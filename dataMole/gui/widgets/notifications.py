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

from datetime import datetime
from typing import Union

from PySide2 import QtGui
from PySide2.QtCore import Slot
from PySide2.QtGui import QIcon, Qt, QPixmap
from PySide2.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QVBoxLayout, QMessageBox, \
    QStyle

# noinspection PyUnresolvedReferences
from dataMole import qt_resources
from dataMole.gui import utils as widgets


class Notifier:
    def __init__(self, parent: QWidget = None):
        self.mNotifier: _NotificationWidget = _NotificationWidget(parent)

    def setParent(self, parent: QWidget) -> None:
        self.mNotifier.setParent(parent)

    def addMessage(self, title: str, message: str,
                   icon: Union[QMessageBox.Icon, QStyle.StandardPixmap, None] = None) -> None:
        self.mNotifier.setNotify(title, message, icon)

    def clearMessages(self) -> None:
        while self.mNotifier.mainLayout.count() > 0:
            w = self.mNotifier.mainLayout.takeAt(0).widget()
            w.deleteLater()


class _Message(QWidget):
    WIDTH = 300

    def __init__(self, title: str, message: str,
                 icon: Union[QMessageBox.Icon, QStyle.StandardPixmap, None] = None,
                 parent: QWidget = None):
        super().__init__(parent)
        gLayout = QGridLayout(self)
        self.titleLabel = QLabel(title, self)
        self.titleLabel.setStyleSheet(
            'font-family: Roboto, sans-serif; font-size: 14px; font-weight: bold; padding: 0;')
        self.messageLabel = QLabel(message, self)
        self.messageLabel.setStyleSheet(
            'font-family: Roboto, sans-serif; font-size: 12px; font-weight: normal; padding: 0;')
        self.messageLabel.setWordWrap(True)
        self.buttonClose = QPushButton(self)
        self.buttonClose.setIcon(QIcon(QPixmap(':/resources/icons/close.png')))
        self.buttonClose.setFixedSize(18, 18)
        nextColumn: int = 0
        if icon:
            lIcon = QLabel(self)
            lIcon.setPixmap(widgets.getStandardIcon(icon, size=30))
            lIcon.setFixedSize(35, 35)
            gLayout.addWidget(lIcon, 0, 0, -1, 1)
            nextColumn = 1
        gLayout.addWidget(self.titleLabel, 0, nextColumn)
        gLayout.addWidget(self.messageLabel, 1, nextColumn)
        gLayout.addWidget(self.buttonClose, 0, nextColumn + 1, -1, 1)
        self.setFixedWidth(_Message.WIDTH)


class _NotificationWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        time = datetime.now()
        currentTime = str(time.hour) + ":" + str(time.minute) + "_"
        self.LOG_TAG = currentTime + self.__class__.__name__ + ": "
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.nMessages = 0
        self.mainLayout = QVBoxLayout(self)

    def updatePosition(self) -> None:
        parentOrigin = self.parentWidget().pos()
        parentSize = self.parentWidget().size()
        # Move in bottom right corner
        self.move(parentOrigin.x() + parentSize.width() - self.width(),
                  parentOrigin.y() + parentSize.height() - self.height())

    def setNotify(self, title, message, icon):
        m = _Message(title, message, icon, self)
        self.mainLayout.addWidget(m)
        m.buttonClose.clicked.connect(self.onClicked)
        self.nMessages += 1
        if not self.isVisible():
            self.show()
        m.show()
        self.adjustSize()
        self.updatePosition()

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        if self.nMessages > 0:
            super().showEvent(event)

    @Slot()
    def onClicked(self):
        self.mainLayout.removeWidget(self.sender().parent())
        self.sender().parent().deleteLater()
        self.nMessages -= 1
        self.adjustSize()
        self.updatePosition()
        if self.nMessages == 0:
            self.hide()
