# from ..frame import AttributeTableModel
import os
from typing import Iterable, Optional

from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import QWidget, QButtonGroup, QRadioButton, QFileDialog, QLineEdit, QHBoxLayout, \
    QPushButton, QLabel, QVBoxLayout, QTableView, QCheckBox

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
                nameLabel = QLabel('Select a name:', self)
                self.nameField = QLineEdit(self)
                self.nameErrorLabel = QLabel(self)

                self.file_layout = QVBoxLayout()
                fileChooserLayout = QHBoxLayout()
                nameRowLayout = QHBoxLayout()
                fileChooserLayout.addWidget(openFileChooser)
                fileChooserLayout.addWidget(self.filePath)
                nameRowLayout.addWidget(nameLabel, 1, Qt.AlignLeft)
                nameRowLayout.addWidget(self.nameField, 2, Qt.AlignRight)
                self.fileErrorLabel = QLabel(self)
                self.file_layout.addLayout(fileChooserLayout)
                self.file_layout.addWidget(self.fileErrorLabel)
                self.file_layout.addLayout(nameRowLayout)
                self.file_layout.addWidget(self.nameErrorLabel)
                self.fileErrorLabel.hide()
                self.nameErrorLabel.hide()
                table_preview = QTableView()
                self.nameField.textEdited.connect(self.nameErrorLabel.hide)

                # Split file by row
                splitRowLayout = QHBoxLayout()
                self.checkSplit = QCheckBox('Split file by rows', self)
                self.numberRowsChunk = QLineEdit(self)
                self.numberRowsChunk.setPlaceholderText('Number of rows per chunk')
                self.numberRowsChunk.setValidator(QIntValidator(self))
                splitRowLayout.addWidget(self.checkSplit)
                splitRowLayout.addWidget(self.numberRowsChunk)
                self.checkSplit.stateChanged.connect(self.toggleSplitRows)

                layout = QVBoxLayout()
                layout.addLayout(self.file_layout)
                layout.addWidget(lab)
                layout.addLayout(button_layout)
                layout.addLayout(splitRowLayout)
                layout.addWidget(QLabel('Preview'))
                layout.addWidget(table_preview)
                self.setLayout(layout)

            @Slot(str)
            def checkFileExists(self, path: str) -> None:
                file_exists = os.path.isfile(path)
                if not file_exists:
                    self.fileErrorLabel.setText('File does not exists!')
                    self.fileErrorLabel.setStyleSheet('color: red')
                    self.filePath.setToolTip('File does not exists!')
                    self.filePath.setStyleSheet('border: 1px solid red')
                    # self.file_layout.addWidget(self.fileErrorLabel)
                    self.parentWidget().disableOkButton()
                    self.fileErrorLabel.show()
                else:
                    # self.file_layout.removeWidget(self.fileErrorLabel)
                    self.fileErrorLabel.hide()
                    self.filePath.setStyleSheet('')
                    self.parentWidget().enableOkButton()
                    if not self.nameField.text():
                        name: str = os.path.splitext(os.path.basename(path))[0]
                        self.nameField.setText(name)

            @Slot(Qt.CheckState)
            def toggleSplitRows(self, state: Qt.CheckState) -> None:
                if state == Qt.Checked:
                    self.numberRowsChunk.setEnabled(True)
                else:
                    self.numberRowsChunk.setDisabled(True)

            def showNameError(self, msg: str) -> None:
                self.nameErrorLabel.setText(msg)
                self.nameErrorLabel.setStyleSheet('color: red')
                self.nameErrorLabel.show()

        self.mywidget = MyWidget(self)
        self.errorHandlers['nameError'] = self.mywidget.showNameError
        return self.mywidget

    def getOptions(self) -> Iterable:
        path: str = self.mywidget.filePath.text()
        sep: int = self.mywidget.separator.checkedId()
        path = path if path else None
        sep_s: str = self.mywidget.buttons_id_value[sep][1] if sep != -1 else None
        chunksize = int(self.mywidget.numberRowsChunk.text()) if self.mywidget.checkSplit.isChecked() \
            else None
        varName: str = self.mywidget.nameField.text()
        return path, sep_s, varName, chunksize

    def setOptions(self, path: Optional[str], sep: Optional[str], name: Optional[str],
                   splitByRow: Optional[int]) -> None:
        # Filepath
        self.mywidget.filePath.setText(path if path else '')
        # Separator
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
        # Variable name
        self.mywidget.nameField.setText(name if name else '')
        # Split by row
        self.mywidget.checkSplit.setChecked(bool(splitByRow and splitByRow > 0))
        self.mywidget.toggleSplitRows(self.mywidget.checkSplit.checkState())
