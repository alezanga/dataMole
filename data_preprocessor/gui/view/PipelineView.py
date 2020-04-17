from PySide2.QtWidgets import QTableView, QWidget

from data_preprocessor.gui.delegate.OperationDelegate import OperationDelegate


class PipelineView(QTableView):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setSelectionMode(QTableView.MultiSelection)
        self.setSelectionBehavior(QTableView.SelectRows)
        delegate = OperationDelegate(parent)
        self.setItemDelegate(delegate)
