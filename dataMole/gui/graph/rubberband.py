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
Custom rubber band selection aimed at being more efficient than the
default one with a large numbers of items
"""

from PySide2 import QtCore, QtGui, QtWidgets
# from .node import GraphNode
# from .edge import GraphEdge

# from constant import DEBUG


class RubberBand(QtWidgets.QGraphicsItem):

    """
    Draw outline of a rectangle (as a shape)

    """

    REPLACE_SELECTION = 1
    ADD_SELECTION = 2
    MINUS_SELECTION = 4
    TOGGLE_SELECTION = 8

    def __init__(self, init_pos, outline=2):
        """Creates an instance of this class

        :param init_pos: Point of origin of the rubber band
        :type init_pos: :class:`QtCore.QPointF`

        :param scene: GraphicsScene that holds the source and target nodes
        :type scene: :class:`nodegraph.scene.GraphScene`

        :param outline: Width of the edge and arrow outline
        :type outline: int

        :returns: An instance of this class
        :rtype: :class:`nodegraph.rubberband.RubberBand`

        """
        QtWidgets.QGraphicsItem.__init__(self, parent=None)

        self._source_pos = init_pos
        self._mouse_pos = init_pos
        self._outline = outline
        self._shape = None
        self._selection_mode = self.REPLACE_SELECTION

        # Settings
        self.setZValue(10)

        # Update
        self._update()

    def _update(self):
        """Update internal properties

        """
        # Update path
        self._shape = QtGui.QPainterPath()
        poly = QtGui.QPolygonF([
            self._source_pos,
            QtCore.QPointF(self._mouse_pos.x(), self._source_pos.y()),
            self._mouse_pos,
            QtCore.QPoint(self._source_pos.x(), self._mouse_pos.y())
        ])
        self._shape.addPolygon(poly)
        self._shape.closeSubpath()

    def update(self):
        """Re-implement update of QtGraphicsItem

        """
        # Update internal containers
        self._update()

        QtWidgets.QGraphicsLineItem.update(self)

    def shape(self):
        """Re-implement shape method
        Return a QPainterPath that represents the bounding shape

        """
        return self._shape

    def boundingRect(self):
        """Re-implement bounding box method

        """
        # Infer bounding box from shape
        return self._shape.controlPointRect()

    def paint(self, painter, option, widget=None):
        """Re-implement paint method

        """
        # Define pen
        palette = (self.scene().palette() if self.scene()
                   else option.palette)
        pen = QtGui.QPen()
        pen.setBrush(palette.highlight())
        pen.setCosmetic(True)
        pen.setWidth(self._outline)
        pen.setStyle(QtCore.Qt.DashLine)

        # Draw Shape
        painter.setPen(pen)
        # painter.drawPath(self._shape)

        color = palette.highlight().color()
        color.setAlphaF(0.2)
        painter.setBrush(QtGui.QColor(color))
        painter.drawRect(self.shape().controlPointRect())

        return

    def refresh(self, mouse_pos=None, init_pos=None):
        """Update corner of rubber band defined by mouse pos

        :param mouse_pos: GraphScene position of the mouse
        :type mouse_pos: :class:`QtCore.QPointF`

        """
        if mouse_pos:
            self._mouse_pos = mouse_pos
        if init_pos:
            self._source_pos = init_pos

        # self.scene().setSelectionArea(self.shape(),
        #                               QtCore.Qt.ContainsItemBoundingRect)
        self.prepareGeometryChange()
        self.update()

    def update_scene_selection(self, operation=None, intersect=None):
        """Update scene selection from the current rubber band bounding box

        :param operation: Replace, add or remove from the current selection
        :type operation: int

        :param intersect:
            Specify how items are selected, by default the item bounding box
            must be fully contained
        :type intersect: :class:`QtCore.Qt.ItemSelectionMode`

        """
        operation = operation or self.REPLACE_SELECTION
        intersect = intersect or QtCore.Qt.ContainsItemBoundingRect

        if operation == self.ADD_SELECTION:
            current_selection = self.scene().selectedItems()
            self.scene().setSelectionArea(self.shape(), intersect)

            for item in current_selection:
                item.setSelected(True)

        elif operation == self.MINUS_SELECTION:
            items = self.scene().items(self.shape(), intersect)

            for item in items:
                item.setSelected(False)

        elif operation == self.TOGGLE_SELECTION:
            items = self.scene().items(self.shape(), intersect)

            for item in items:
                if item.isSelected():
                    item.setSelected(False)
                else:
                    item.setSelected(True)
        else:
            self.scene().setSelectionArea(self.shape(), intersect)
