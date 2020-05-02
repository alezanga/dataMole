from PySide2.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem

ops = ['a', 'bb', '333', 'fff']


def string_to_item(name: str):
    return QTreeWidgetItem([name])


class OperationMenu(QTreeWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        top_items = list(map(string_to_item, ['Input', 'Output', 'All']))
        self.addTopLevelItems(top_items)
