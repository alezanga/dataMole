from PySide2.QtCore import Slot, QModelIndex, Qt
from PySide2.QtWidgets import QWidget, QLabel, QFormLayout

from data_preprocessor.gui.workbench import WorkbenchModel

# TODO this

class FramePanel(QWidget):
    def __init__(self, w: WorkbenchModel, parent=None):
        super().__init__(parent)
        labeln = QLabel('Name:', self)
        labelc = QLabel('Columns:', self)
        labelr = QLabel('Rows:', self)
        labeli = QLabel('Index:', self)
        self.name = QLabel(self)
        self.rows = QLabel(self)
        self.columns = QLabel(self)
        self.index = QLabel(self)
        layout = QFormLayout(self)
        layout.addRow(labeln, self.name)
        layout.addRow(labelr, self.rows)
        layout.addRow(labelc, self.columns)
        layout.addRow(labeli, self.index)
        self.__w = w

    def updateData(self, row: int) -> None:
        index = self.__w.index(row, 0, QModelIndex())
        name = index.data(Qt.DisplayRole)
        frameModel = self.__w.getDataframeModelByIndex(row)
        self.name.setText(name)
        self.columns.setText(str(frameModel.columnCount()))
        self.rows.setText(str(frameModel.rowCount()))
        index = frameModel.frame.shape.index
        self.index.setText(index if index else 'default')
        frameModel.columnsRemoved.connect()

    def nameChanged(self) -> None:
        pass

    @Slot(str)
    def infoChanged(self, name: str, rows: int, columns: int) -> None:
        self.name.setText(name)
        self.columns.setText(str(columns))
        self.rows.setText(str(rows))
