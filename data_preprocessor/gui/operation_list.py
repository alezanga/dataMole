import importlib
from typing import Callable, List

from PySide2.QtCore import Qt, QPoint, QMimeData
from PySide2.QtGui import QMouseEvent, QDrag
from PySide2.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QApplication


def _build_item(name: str, data=None) -> QTreeWidgetItem:
    """
    Build a tree item with a display name, and sets its data

    @:param data: the class name. If specified it's set at column 1 on Qt.UserRole
    """
    item = QTreeWidgetItem([name])
    flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
    if data:
        item.setData(1, Qt.UserRole, data)
        flags |= Qt.ItemIsDragEnabled
    item.setFlags(flags)
    return item


def _addChildren(parents: List[QTreeWidgetItem], op_class: Callable) -> None:
    op_name = getattr(op_class, 'name')()
    op_input: bool = getattr(op_class, 'maxInputNumber')() == 0
    op_output: bool = getattr(op_class, 'minOutputNumber')() == 0
    if op_input:
        parents[0].addChild(_build_item(op_name, data=op_class))
    elif op_output:
        parents[1].addChild(_build_item(op_name, data=op_class))
    else:
        parents[2].addChild(_build_item(op_name, data=op_class))


class OperationMenu(QTreeWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.__dragStartPosition: QPoint = None
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        # Parent items (categories)
        top_items = list(map(_build_item, ['Input', 'Output', 'All']))
        self.addTopLevelItems(top_items)
        # Import everything in operations directory
        from data_preprocessor.operation import __all__
        var_export = 'export'
        for module_name in __all__:
            module = importlib.import_module('.' + module_name, package='data_preprocessor.operation')
            if not hasattr(module, var_export):
                continue
            op_class = getattr(module, var_export)
            if isinstance(op_class, list):
                for c in op_class:
                    _addChildren(top_items, c)
            else:
                _addChildren(top_items, op_class)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.__dragStartPosition: QPoint = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not event.buttons() and Qt.LeftButton:
            return
        # Test if item is drag enabled
        clicked_item = self.itemAt(self.__dragStartPosition)
        if clicked_item and not bool(clicked_item.flags() & Qt.ItemIsDragEnabled):
            return
        if (event.pos() - self.__dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return

        drag: QDrag = QDrag(self)
        mimeData: QMimeData = QMimeData()
        mimeData.setText('operation')

        drag.setMimeData(mimeData)
        drag.exec_()

    def getDropData(self) -> Callable:
        op = self.itemAt(self.__dragStartPosition).data(1, Qt.UserRole)
        self.__dragStartPosition = None
        return op
