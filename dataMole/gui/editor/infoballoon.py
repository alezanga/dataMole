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

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QLabel, QPushButton, QSizePolicy, QFrame, QVBoxLayout, \
    QTextBrowser


class InfoBalloon(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle('Operation helper')
        self.body = QTextBrowser(self)
        self.body.setOpenExternalLinks(True)
        closeButton = QPushButton('Close', self)
        self.body.setBackgroundRole(QLabel().backgroundRole())
        self.setWindowFlags(Qt.Tool)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.body.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setMinimumWidth(500)
        self.setMaximumWidth(1000)
        closeButton.clicked.connect(self.close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.body)
        layout.addWidget(closeButton, 0, Qt.AlignHCenter)

    def setText(self, text: str) -> None:
        self.body.setHtml(text)
        self.body.document().setTextWidth(500)
        self.body.document().adjustSize()
        self.resize(500, self.body.document().size().height())
