from typing import Tuple, Dict

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTableView, QHeaderView, QPushButton, QHBoxLayout, QVBoxLayout

from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.gui.model import AttributeTableModel


class RenameEditor(AbsOperationEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Rename operation editor')
        self.__model = AttributeTableModel(self, checkable=False, editable=True)
        self.__view = QTableView()
        self.__view.setModel(self.__model)
        header = self.__view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.__view.setHorizontalHeader(header)

        butOk = QPushButton('Ok')
        butCancel = QPushButton('Cancel')
        butLayout = QHBoxLayout()
        butLayout.addWidget(butCancel, alignment=Qt.AlignLeft)
        butLayout.addWidget(butOk, alignment=Qt.AlignRight)

        layout = QVBoxLayout()
        layout.addWidget(self.__view)
        layout.addLayout(butLayout)
        self.setLayout(layout)
        self.setFocusPolicy(Qt.StrongFocus)

        butOk.pressed.connect(self.acceptAndClose)
        butCancel.pressed.connect(self.rejectAndClose)

    def getOptions(self) -> Dict[int, str]:
        return self.__model.editedAttributes()

    def setOptions(self, option: Tuple) -> None:
        self.__model.setEditedAttributes(option)
