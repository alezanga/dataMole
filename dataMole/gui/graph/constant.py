# -*- coding: utf-8 -*-
#
# Authors:      Alessandro Zangari (alessandro.zangari.code@outlook.com)
#               Nicolas Darques    (dsideb@gmail.com)
# Copyright:    © Copyright 2020 Alessandro Zangari, Università degli Studi di Padova
# License:      GPL-3.0-or-later
# Date:         2020-10-04
# Version:      1.0
#
# This file contains parts taken from "Nodegraph-pyqt" available at
# https://github.com/dsideb/nodegraph-pyqt
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

"""
Constants used in "graph" package
"""

from PySide2 import QtCore, QtGui

SCENE_WIDTH = 8000000
SCENE_HEIGHT = 4000000

DEBUG = False

# Constant shapes

height = 4
width = height * 3 / 4
thick = height / 2

ARROW_SLIM = QtGui.QPolygonF([QtCore.QPointF(thick / 2, 0),
                              QtCore.QPointF(- thick, - width),
                              QtCore.QPointF(- thick * 2, - width),
                              QtCore.QPointF(- thick / 2, 0),
                              QtCore.QPointF(- thick * 2, width),
                              QtCore.QPointF(- thick, width)])

ARROW_STANDARD = QtGui.QPolygonF([QtCore.QPointF(height, 0),
                                  QtCore.QPointF(- height, - width),
                                  QtCore.QPointF(- height, width),
                                  QtCore.QPointF(height, 0)])
