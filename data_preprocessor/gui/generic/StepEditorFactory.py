from PySide2.QtCore import QAbstractItemModel, QSize, Qt, Slot
from PySide2.QtWidgets import QLabel, QLineEdit, QComboBox, QGridLayout, QHBoxLayout, QCheckBox, \
    QVBoxLayout, QPushButton, QDialog
from PySide2.QtGui import QValidator
from data_preprocessor.gui.generic.AbsStepEditor import AbsStepEditor
from typing import Dict, List, Callable
from data_preprocessor.decorators.generic import singleton
import PySide2.QtGui


@singleton
class StepEditorFactory:
    def __init__(self):
        self.__mainLayout: QVBoxLayout = None
        self.__layout: QGridLayout = None
        self.__editor: AbsStepEditor = None
        self.__optionsGetter: List[Callable] = list()

    def initEditor(self, title: str = '') -> None:
        """
        Initializes an editor object clearing the internal state.
        You should call this method every time you need to generate a new editor.
        """

        class ConcreteStep(AbsStepEditor):
            def getOptions(self) -> Dict:
                pass

        self.__layout = QGridLayout()
        self.__editor = ConcreteStep()
        self.__optionsGetter = list()
        self.__editor.setWindowTitle('Generic editor' if not title else title)
        self.__layout.setHorizontalSpacing(30)
        self.__mainLayout = QVBoxLayout()
        self.__mainLayout.setDirection(QVBoxLayout.BottomToTop)
        buttons = QHBoxLayout()
        cancelBut = QPushButton('Cancel')
        okBut = QPushButton('Ok')
        buttons.addWidget(cancelBut, alignment=Qt.AlignLeft)
        buttons.addWidget(okBut, alignment=Qt.AlignRight)
        self.__mainLayout.addLayout(buttons)
        cancelBut.clicked.connect(self.__editor.reject())
        okBut.clicked.connect(self.__editor.accept())

    def addTextField(self, label: str, validator: QValidator = None, tooltip: str = '') -> None:
        row: int = self.__layout.rowCount()
        self.__layout.addWidget(QLabel(label), row, 0)
        textEdit = QLineEdit()
        if tooltip: textEdit.setToolTip(tooltip)
        if validator: textEdit.setValidator(validator)
        self.__layout.addWidget(textEdit, row, 1)
        self.__optionsGetter.append(textEdit.text)

    def addComboBox(self, label: str, options: QAbstractItemModel, tooltip: str = '') -> None:
        row: int = self.__layout.rowCount()
        self.__layout.addWidget(QLabel(label), row, 0)
        combo = QComboBox()
        if tooltip: combo.setToolTip(tooltip)
        options.setParent(combo)
        combo.setModel(options)
        self.__layout.addWidget(combo, row, 1)
        self.__optionsGetter.append(combo.currentText)

    def addCheckBox(self, label: str, tooltip: str = '') -> None:
        row: int = self.__layout.rowCount()
        checkbox = QCheckBox(label)
        if tooltip: checkbox.setToolTip(tooltip)
        self.__layout.addWidget(checkbox, row, 1)
        self.__optionsGetter.append(checkbox.isChecked)

    def setSizeHint(self, width: int, height: int):
        self.__editor.sizeHint = lambda: QSize(width, height)

    def getEditor(self) -> AbsStepEditor:
        def getter() -> List:
            return [f() for f in self.__optionsGetter]

        # @Slot(int)
        # def closeDialog(c: int):
        #     if c == QDialog.Accepted:
        #         return self.getOptions()
        #     else:
        #         return []

        # self.__editor.finished[int].connect(closeDialog)
        self.__mainLayout.addLayout(self.__layout)
        self.__editor.setLayout(self.__mainLayout)
        self.__editor.getOptions = getter
        return self.__editor
