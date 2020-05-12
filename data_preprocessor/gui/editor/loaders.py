# from ..frame import AttributeTableModel
import os
from typing import Iterable, Optional

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QButtonGroup, QRadioButton, QFileDialog, QLineEdit, QHBoxLayout, \
    QPushButton, QLabel, QVBoxLayout, QTableView

from .interface import AbsOperationEditor


class LoadCSVEditor(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        class MyWidget(QWidget):
            def __init__(self, parent):
                super().__init__(parent)
                self.buttons_id_value = {
                    1: ('comma', ','),
                    2: ('space', '\\s'),
                    3: ('tab', '\t'),
                    4: ('semicolon', ';')
                }
                self.separator = QButtonGroup()
                lab = QLabel()
                lab.setText('Choose a separator:')
                for bid, value in self.buttons_id_value.items():
                    self.separator.addButton(QRadioButton(value[0]), id=bid)
                self.separator.setExclusive(True)
                self.default_button = self.separator.button(1)
                button_layout = QHBoxLayout()
                for button in self.separator.buttons():
                    button_layout.addWidget(button)

                openFileChooser = QPushButton('Choose')
                fileChooser = QFileDialog(self, 'Open csv', str(os.getcwd()), 'Csv (*.csv)')
                fileChooser.setFileMode(QFileDialog.ExistingFile)
                self.filePath = QLineEdit()
                openFileChooser.released.connect(fileChooser.show)
                fileChooser.fileSelected.connect(self.filePath.setText)
                self.filePath.textChanged.connect(self.checkFileExists)

                self.file_layout = QVBoxLayout()
                fileChooserLayout = QHBoxLayout()
                fileChooserLayout.addWidget(openFileChooser)
                fileChooserLayout.addWidget(self.filePath)
                self.error_label = QLabel(self)
                self.file_layout.addLayout(fileChooserLayout)
                self.file_layout.addWidget(self.error_label)
                self.error_label.hide()
                table_preview = QTableView()

                layout = QVBoxLayout()
                layout.addLayout(self.file_layout)
                layout.addWidget(lab)
                layout.addLayout(button_layout)
                layout.addWidget(QLabel('Preview'))
                layout.addWidget(table_preview)
                self.setLayout(layout)

            @Slot(str)
            def checkFileExists(self, path: str) -> None:
                file_exists = os.path.isfile(path)
                if not file_exists:
                    self.error_label.setText('File does not exists!')
                    self.error_label.setStyleSheet('color: red')
                    self.filePath.setToolTip('File does not exists!')
                    self.filePath.setStyleSheet('border: 1px solid red')
                    # self.file_layout.addWidget(self.error_label)
                    self.parentWidget().disableOkButton()
                    self.error_label.show()
                else:
                    # self.file_layout.removeWidget(self.error_label)
                    self.error_label.hide()
                    self.filePath.setStyleSheet('')
                    self.parentWidget().enableOkButton()

        self.mywidget = MyWidget(self)
        return self.mywidget

    def getOptions(self) -> Iterable:
        path: str = self.mywidget.filePath.text()
        sep: int = self.mywidget.separator.checkedId()
        path = path if path else None
        sep_s: str = self.mywidget.buttons_id_value[sep][1] if sep != -1 else None
        return path, sep_s

    def setOptions(self, path: Optional[str], sep: Optional[str]) -> None:
        self.mywidget.filePath.setText(path if path else '')
        button_id: int = -1
        for bid, v in self.mywidget.buttons_id_value.items():
            if v == sep:
                button_id = bid
                break
        button = self.mywidget.separator.button(button_id)
        if button:
            button.setChecked(True)
        else:
            self.mywidget.default_button.setChecked(True)
