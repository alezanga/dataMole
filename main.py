# This Python file uses the following encoding: utf-8
import sys

from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTableView

from data_preprocessor.data import Frame
from data_preprocessor.gui.model import AttributeTableModel
from data_preprocessor.gui.model.FrameModel import FrameModel


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
        f = Frame(d)
        # pw = PipelineWidget(self, f)
        frameModel = FrameModel(self, f)
        frameView = QTableView(self)
        frameView.setModel(frameModel)

        attributeTable = AttributeTableModel(self, True, True)
        attributeTable.setSourceModel(frameModel)
        attributeView = QTableView(self)
        attributeView.setModel(attributeTable)

        layout = QHBoxLayout()
        layout.addWidget(frameView)
        layout.addWidget(attributeView)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.setCentralWidget(MainWidget())
    window.show()
    sys.exit(app.exec_())
