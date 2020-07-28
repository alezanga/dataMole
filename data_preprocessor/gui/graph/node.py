# =============================================================================
# Nodegraph-pyqt
#
# Everyone is permitted to copy and distribute verbatim copies of this
# document, but changing it is not allowed without permissions.
#
# For any questions, please contact: dsideb@gmail.com
#
# GNU LESSER GENERAL PUBLIC LICENSE (Version 3, 29 June 2007)
# =============================================================================

"""
Base node definition including:

    * Node
    * NodeSlot

"""
# import sha
from typing import Union, Set, List

from PySide2 import QtCore, QtGui, QtWidgets

from data_preprocessor.status import NodeStatus
from .constant import DEBUG

_statusShow = {
    NodeStatus.NONE: ('', None),
    NodeStatus.SUCCESS: ('completed', QtGui.QColor(50, 205, 50)),
    NodeStatus.ERROR: ('error', QtGui.QColor(220, 20, 60)),
    NodeStatus.PROGRESS: ('in progress', QtGui.QColor(255, 255, 0))
}


class Node(QtWidgets.QGraphicsItem):
    """
    Base class for node graphic item

    As much as possible, everything is drawn in the node paint function for
    performance reasons
    """

    @staticmethod
    def __headerSize(text: str, font: QtGui.QFont) -> QtCore.QSize:
        """ Returns the proper header size with respect to a given string and font """
        metrics = QtGui.QFontMetrics(font)
        return metrics.size(QtCore.Qt.TextSingleLine, text + '      ')

    def __init__(self, name: str, id: int, inputs=None, parent: QtWidgets.QGraphicsItem = None,
                 output: bool = True):
        """Create an instance of this class

        """
        super().__init__(parent)
        if inputs is None:
            inputs = list()
        self._name = name
        self._id = id
        # Set font used for label (operation name)
        self._title_font = QtGui.QFont("Arial", 14)
        # Compute size of label to display
        self._width = max(130, Node.__headerSize(self._name, self._title_font).width())
        self._height = 130
        self._outline = 6
        self._slot_radius = 10
        self._label_height = 34
        self._bbox = None  # cache container
        self._round_slot = None
        self._rect_slot = None
        self._hover_slot = False
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable |
                      QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.setAcceptHoverEvents(False)

        # Build output slot
        self._output = NodeSlot(name="out", parent=self, family=NodeSlot.OUTPUT) if output else None

        # Build input slots
        self._inputs = []
        for i, slot_name in enumerate(inputs):
            an_input = NodeSlot(name=slot_name, parent=self, position=i)
            self._inputs.append(an_input)

        self._status = NodeStatus.NONE
        self._status_slot = NodeSlot(name=None, parent=self, family=NodeSlot.STATUS)

        # Update internal containers
        self._update()

    @property
    def name(self):
        """Returns the name of the node

        """
        return self._name

    @property
    def id(self) -> int:
        return self._id

    @property
    def status(self) -> NodeStatus:
        return self._status

    @status.setter
    def status(self, s) -> None:
        self._status = s

    @property
    def edges(self):
        """Return all hashes of connected edges

        """
        outputs = self._output.edge if self._output else []
        inputs = list(set([e for i in self._inputs for e in i.edge]))
        return set(outputs + inputs)

    @property
    def slots(self) -> List['NodeSlot']:
        return self._inputs + ([self._output] if self._output else [])

    def _update(self):
        """Update slots internal properties

        """
        slot_height = self._slot_radius * 2 + self._outline
        base_y = self._height / 2 + self._label_height / 2 + self._outline / 2

        # Update base slot bounding box
        self._draw_slot = QtCore.QRectF(0,
                                        0,
                                        self._slot_radius * 2,
                                        self._slot_radius * 2)
        # Update output
        if self._output:
            init_y = base_y - slot_height / 2
            self._output.rect = QtCore.QRectF(self._draw_slot).translated(
                self._width - self._slot_radius, init_y)

        # Update status
        bbox_plus_status = 0
        if self._status != NodeStatus.NONE:
            bbox_plus_status = self._slot_radius
            init_y = self._outline / 2 - slot_height / 2
            self._status_slot.rect = QtCore.QRectF(self._draw_slot).translated(
                self._width - self._slot_radius, init_y)

        # Update inputs
        init_y = base_y - slot_height * len(self._inputs) / 2
        for i, _input in enumerate(self._inputs):
            self._inputs[i].rect = QtCore.QRectF(self._draw_slot).translated(
                -self._slot_radius, init_y + slot_height * i)

        # Update bounding box
        self._bbox = QtCore.QRectF(
            -self._outline / 2 - self._slot_radius,
            -self._outline / 2 - bbox_plus_status,
            self._width + self._outline + self._slot_radius * 2,
            self._height + self._outline + bbox_plus_status)

    def _update_hover_slot(self, slot):
        if slot == self._hover_slot:
            # No change
            return

        self._hover_slot = slot

        self.update()

    def boundingRect(self):
        """Return a QRect that represents the bounding box of the node.
        Here that sould be the bounding box of the primary shape of the node.

        """
        return self._bbox

    def paint(self, painter, option, widget=None):
        """Re-implement paint method

        """
        # print("Redraw %s" % self._name)
        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        # Resolve fill, text and outlines brush
        fill_brush = self.scene().palette().button()
        text_brush = self.scene().palette().text()
        if option.state & QtWidgets.QStyle.State_Selected:
            fill_brush = self.scene().palette().highlight()
            text_brush = self.scene().palette().highlightedText()

        # Set brush and pen, then start drawing
        painter.setBrush(self.scene().palette().buttonText())
        painter.setPen(QtGui.QPen(fill_brush, self._outline))

        # Draw primary shape
        painter.drawRect(0, 0, self._width, self._height)

        # Draw label background
        # TODO: Color should be based on node type
        painter.setBrush(QtGui.QColor(90, 90, 140))
        painter.setPen(QtCore.Qt.NoPen)
        label_rect = QtCore.QRectF(self._outline / 2,
                                   self._outline / 2,
                                   self._width - self._outline,
                                   self._label_height - self._outline / 2)
        painter.drawRect(label_rect)

        # Draw text
        if lod >= 0.4:
            font = self._title_font
            font.setStyleStrategy(QtGui.QFont.ForceOutline)
            painter.setFont(font)
            painter.setPen(QtGui.QPen(text_brush, 1))
            painter.scale(1, 1)
            painter.drawText(label_rect, QtCore.Qt.AlignCenter, self._name)

        # Draw slots
        if lod >= 0.15:
            # Should be driven by slot type
            hover_color = QtGui.QColor(90, 90, 140)
            hover_normal = self.scene().palette().text()
            self.setAcceptHoverEvents(True)
            painter.setBrush(hover_normal)
            painter.setPen(QtGui.QPen(fill_brush, self._outline))

            if lod >= 0.35:
                # Draw output (Ellipse)
                if self._output:
                    if self._hover_slot == self._output:
                        # Hover color should be driven by slot type
                        painter.setBrush(hover_color)
                    painter.drawEllipse(self._output._rect)

                if self._status != NodeStatus.NONE:
                    if self._hover_slot == self._status_slot:
                        self.setToolTip('status: {}'.format(_statusShow[self._status][0]))
                    color = _statusShow[self._status][1]
                    painter.setBrush(hover_normal if not color else color)
                    painter.drawEllipse(self._status_slot.rect)

                # Draw input (Ellipse)
                for aninput in self._inputs:
                    if self._hover_slot == aninput:
                        painter.setBrush(hover_color)
                    else:
                        painter.setBrush(hover_normal)
                    painter.drawEllipse(aninput.rect)
            else:
                # Draw output (Rectangle)
                if self._output:
                    if self._hover_slot == self._output:
                        painter.setBrush(hover_color)
                    painter.drawRect(self._output._rect)

                if self._status != NodeStatus.NONE:
                    if self._hover_slot == self._status_slot:
                        self.setToolTip('status: {}'.format(_statusShow[self._status][0]))
                    color = _statusShow[self._status][1]
                    painter.setBrush(hover_normal if not color else color)
                    painter.drawRect(self._status_slot.rect)

                # Draw input (Rectangle)
                for aninput in self._inputs:
                    if self._hover_slot == aninput:
                        painter.setBrush(hover_color)
                    else:
                        painter.setBrush(hover_normal)
                    painter.drawRect(aninput.rect)
        else:
            self.setAcceptHoverEvents(False)

        # Draw slot labels
        if lod >= 0.5:
            font = QtGui.QFont("Arial", 11)
            font.setStyleStrategy(QtGui.QFont.ForceOutline)
            painter.setFont(font)
            painter.setPen(QtGui.QPen(self.scene().palette().text(), 1))

            width = self._width / 2 - self._slot_radius - self._outline
            height = self._slot_radius * 2

            # Output
            if self._output:
                alignment = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
                rect = QtCore.QRectF(self._width / 2,
                                     self._output._rect.top(),
                                     width,
                                     height)
                painter.drawText(rect, alignment, self._output.name)
                # painter.setBrush(QtCore.Qt.NoBrush)
                # painter.drawRect(rect)

            # Input
            alignment = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            for aninput in self._inputs:
                rect = QtCore.QRectF(self._slot_radius + self._outline,
                                     aninput._rect.top(),
                                     width,
                                     height)
                painter.drawText(rect, alignment, aninput.name)
                # painter.setBrush(QtCore.Qt.NoBrush)
                # painter.drawRect(rect)

        # Draw debug
        if DEBUG:
            painter.setBrush(QtGui.QBrush())
            painter.setPen(QtGui.QColor(255, 0, 0))
            painter.drawRect(self.boundingRect())

        return

    def hoverMoveEvent(self, event):
        """Re-implement Mouse hover move event

        :param event: Hover move event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        # print("NODE %s hover move" % self._name)
        his = [i for i in self._inputs if i._rect.contains(event.pos())]
        if self._output and self._output._rect.contains(event.pos()):
            self._update_hover_slot(self._output)
        elif his:
            self._update_hover_slot(his[0])
        else:
            self._update_hover_slot(False)

        # Call normal behavior
        QtWidgets.QGraphicsItem.hoverMoveEvent(self, event)

        return

    def hoverLeaveEvent(self, event):
        """Re-implement Mouse hover move event

        :param event: Hover move event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        self._update_hover_slot(False)

        # Call normal behavior
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)

    def mousePressEvent(self, event):
        """Re-implement mousePressEvent from base class

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        # print("MOUSE PRESS NODE!")

        buttons = event.buttons()
        # modifiers = event.modifiers()

        if buttons == QtCore.Qt.LeftButton:
            if self._output and self._output._rect.contains(event.pos()):
                mouse_pos = self.mapToScene(event.pos())
                self.scene().start_interactive_edge(self._output, mouse_pos)
                event.accept()
                return
            for aninput in self._inputs:
                if aninput._rect.contains(event.pos()):
                    mouse_pos = self.mapToScene(event.pos())
                    self.scene().start_interactive_edge(aninput, mouse_pos)
                    event.accept()
                    return

        QtWidgets.QGraphicsItem.mousePressEvent(self, event)

    # def mouseReleaseEvent(self, event):
    #     """Re-implement mouseReleaseEvent from base class

    #     :param event: Mouse event
    #     :type event: :class:`QtWidgets.QGraphicsSceneMouseEvent`

    #     """
    #     buttons = event.button()

    #     if buttons == QtCore.Qt.LeftButton:
    #         # if self._output._rect.contains(event.pos()):
    #         print(self._output._rect.contains(event.pos()))
    #         print("DROP")
    #         print(event.pos())
    #         print(self._output._rect)

    #     QtWidgets.QGraphicsItem.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        """Re-implement mouseMoveEvent from base class

        :param event: Mouse event
        :type event: :class:`QtWidgets.QMouseEvent`

        """
        buttons = event.buttons()
        # modifiers = event.modifiers()

        # print("%s : mouse move event. Hover slot: %s" % (self._name, self._hover_slot))

        if buttons == QtCore.Qt.LeftButton:
            if self.scene().is_interactive_edge:
                # Edge creation mode

                # print("Node Name: %s, pos: %s" % (self._name, event.pos()))
                event.accept()
                return

        QtWidgets.QGraphicsItem.mouseMoveEvent(self, event)

    def refresh(self, refresh_edges=True):
        """Refreh node

        :param refresh_edges: If true, also connected edge
        :type refresh_edges: bool

        """
        self.prepareGeometryChange()
        self._update()
        if refresh_edges and self.edges:
            for ahash in self.edges:
                self.scene().edges_by_hash[ahash].refresh()
        self.update()


class NodeSlot(object):
    """
    Base class for edge slot

    """

    INPUT = 0
    OUTPUT = 1
    STATUS = 2

    def __init__(self, name, parent, family=None, position: int = None):
        """Instance this class

        """
        # QtWidgets.QGraphicsItem.__init__(self, parent=parent, scene=scene)
        self._name = name
        self._position: int = position
        self.parent = parent
        self._family = family or self.INPUT
        self._rect = None
        self._edge = set()

    @property
    def name(self):
        """Return the family of the slot

        """
        return self._name

    @property
    def position(self) -> int:
        return self._position

    @property
    def family(self):
        """Return the family of the slot

        """
        return self._family

    @property
    def rect(self):
        """Return bounding box of slot

        """
        return self._rect

    @rect.setter
    def rect(self, value):
        """ Set property rect

        :param value: Rectangle defintion of the slot
        :type value: class::`QtCore.QRectF`

        """
        self._rect = value

    @property
    def center(self):
        """Return center point of the slot in scene coordinates

        """
        return self.parent.mapToScene(self._rect.center())

    @property
    def edge(self):
        """Return hash id of connected edge or None

        :rtype: list

        """
        return list(self._edge)

    @edge.setter
    def edge(self, value):
        """Set property edge (replace)

        :type value: str or list

        """
        self._edge = set(value if isinstance(value, list) else [value])

    @property
    def parentNode(self) -> Node:
        return self.parent

    def add_edge(self, value):
        """Add edge hash(es) to set

        :type value: str or list

        """
        self._edge |= set(value if isinstance(value, list) else [value])

    def remove_edge(self, value: Union[str, List[str], Set[str]]):
        """Remove edge hash(es) from set

        :type value: str or list

        """
        self._edge -= set([value] if isinstance(value, str) else value)
