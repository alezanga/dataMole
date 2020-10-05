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

from PySide2.QtCore import Slot, QUrl, QSize
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QStatusBar, QWidget, QLabel

from dataMole.gui.widgets.waitingspinnerwidget import QtWaitingSpinner


class StatusBar(QStatusBar):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # logButton = QPushButton('Open log', self)
        self._spinner = QtWaitingSpinner(self, centerOnParent=False)
        self._spinner.setInnerRadius(6)
        self.setContentsMargins(5, 1, 5, 1)

        self.addPermanentWidget(self._spinner, 1)
        spacer = QLabel()
        spacer.setFixedSize(QSize(5, 5))
        self.addPermanentWidget(spacer, 0)
        # self.addPermanentWidget(logButton, 0)

        # logButton.pressed.connect(self._openLog)

    @Slot(str)
    def logMessage(self, msg: str) -> None:
        self.showMessage(msg, 10)

    @Slot()
    def startSpinner(self) -> None:
        self._spinner.start()

    @Slot()
    def stopSpinner(self) -> None:
        self._spinner.stop()

    @Slot()
    def _openLog(self) -> None:
        from dataMole.flogging.utils import LOG_PATH
        QDesktopServices.openUrl(QUrl(LOG_PATH))
