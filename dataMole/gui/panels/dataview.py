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

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget


class DataView(QWidget):
    """ An interface to use with data views to be shown in the View panel """

    def __init__(self, workbench, parent=None):
        super().__init__(parent)
        self._workbench = workbench

    @Slot(str, str)
    def onFrameSelectionChanged(self, name: str, oldName: str) -> None:
        """ React to the change of the active frame """
        pass
