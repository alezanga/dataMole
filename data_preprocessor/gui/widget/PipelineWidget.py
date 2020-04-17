from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout

from data_preprocessor.data import Frame
from data_preprocessor.gui.model import PipelineModel
from data_preprocessor.gui.view import PipelineView
from data_preprocessor.operation import Pipeline
from data_preprocessor.operation.attribute.RenameOp import RenameOp


class PipelineWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
        f = Frame(d)
        self.__pipeline = Pipeline(df=f)
        self.__pipeline.add(RenameOp(f.shape))
        self.__model = PipelineModel(self.__pipeline, self)
        self.__view = PipelineView(self)
        self.__view.setModel(self.__model)

        layout = QHBoxLayout()

        butlayout = QVBoxLayout()
        addButton = QPushButton(text='Add')
        # addButton.pressed.connect(self.__model)
        removeButton = QPushButton(text='Remove')
        butlayout.addWidget(addButton, alignment=Qt.AlignTop)
        butlayout.addWidget(removeButton, alignment=Qt.AlignTop)

        layout.addLayout(butlayout)
        layout.addWidget(self.__view)

        self.setLayout(layout)
