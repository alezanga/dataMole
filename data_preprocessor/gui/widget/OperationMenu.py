import importlib

from PySide2.QtCore import Qt, QPoint, QMimeData
from PySide2.QtGui import QMouseEvent, QDrag
from PySide2.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QApplication

from data_preprocessor.operation.interface import Operation


def build_item(name: str, data=None):
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


class OperationMenu(QTreeWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.__dragStartPosition: QPoint = None
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        # Parent items (categories)
        top_items = list(map(build_item, ['Input', 'Output', 'All']))
        self.addTopLevelItems(top_items)
        # Import everything in operations directory
        from data_preprocessor.operation import __all__
        for module_name in __all__:
            module = importlib.import_module('.' + module_name, package='data_preprocessor.operation')
            if not hasattr(module, module_name):
                continue
            op_class = getattr(module, module_name)
            op_name = getattr(op_class, 'name')()
            op_input: bool = getattr(op_class, 'maxInputNumber')() == 0
            op_output: bool = getattr(op_class, 'minOutputNumber')() == 0
            if op_input:
                top_items[0].addChild(build_item(op_name, data=op_class))
            elif op_output:
                top_items[1].addChild(build_item(op_name, data=op_class))
            else:
                top_items[2].addChild(build_item(op_name, data=op_class))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.__dragStartPosition: QPoint = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not event.buttons() and Qt.LeftButton:
            return
        # Test if item is drag enabled
        if not bool(self.itemAt(self.__dragStartPosition).flags() & Qt.ItemIsDragEnabled):
            return
        if (event.pos() - self.__dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return

        drag: QDrag = QDrag(self)
        mimeData: QMimeData = QMimeData()
        mimeData.setText('operation')

        drag.setMimeData(mimeData)
        drag.exec_()

    def getDropData(self) -> Operation:
        op = self.itemAt(self.__dragStartPosition).data(1, Qt.UserRole)()
        self.__dragStartPosition = None
        return op
