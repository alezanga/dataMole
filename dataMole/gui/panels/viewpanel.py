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

from pydoc import locate

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QComboBox, QFormLayout

from . import __classes__, __config__
from .dataview import DataView


class ViewPanel(DataView):
    def __init__(self, workbench, parent: QWidget = None):
        super().__init__(workbench, parent)
        self.__currentFrameName: str = None
        self.__chartTypeCB = QComboBox(self)
        self.fLayout = QFormLayout(self)
        self.fLayout.addRow(__config__['description'], self.__chartTypeCB)
        moduleNames = __classes__.keys()
        self.fLayout.setHorizontalSpacing(40)
        self.__chartTypeCB.addItems(list(moduleNames))
        defaultSelection = __config__['default']
        self.__chartTypeCB.setCurrentText(defaultSelection)
        self.chartSelectionChanged(defaultSelection)
        self.__chartTypeCB.currentTextChanged.connect(self.chartSelectionChanged)

    @Slot(str)
    def chartSelectionChanged(self, text: str) -> None:
        if self.fLayout.rowCount() == 2:
            self.fLayout.removeRow(1)
        widget: type = locate(__classes__[text])  # subclass of DataView
        self.fLayout.addRow(widget(self._workbench, self))
        self.onFrameSelectionChanged(self.__currentFrameName, '')

    @Slot(str, str)
    def onFrameSelectionChanged(self, name: str, oldName: str) -> None:
        self.__currentFrameName = name
        self.fLayout.itemAt(1, QFormLayout.SpanningRole).widget().onFrameSelectionChanged(name, oldName)
