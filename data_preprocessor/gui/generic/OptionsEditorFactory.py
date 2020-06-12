import copy
from typing import Dict, List, Callable, Tuple, Any, Iterable, Optional

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtGui import QValidator
from PySide2.QtWidgets import QLineEdit, QCheckBox, \
    QWidget, QFormLayout, QStyledItemDelegate

from data_preprocessor.decorators.generic import singleton
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from data_preprocessor.gui.editor.optionwidget import RadioButtonGroup
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, AttributeTableModel


class AttributeTableWithOptions(AttributeTableModel):
    def __init__(self, parent: QWidget = None, checkable: bool = False,
                 editable: bool = False, showTypes: bool = True, options: Dict = None):
        super().__init__(parent, checkable, editable, showTypes)
        # options description { key, (label, qvalidator) }
        self._optionsDesc: Dict[str, Tuple[str, QValidator]] = options
        # Column position for each option column
        self._optionsPos: Dict[int, str] = dict()
        self._inverseOptionsPos: Dict[str, int] = dict()
        baseCount = super().columnCount()
        for i, opt in enumerate(self._optionsDesc.keys()):
            self._optionsPos[baseCount + i] = opt
            self._inverseOptionsPos[opt] = baseCount + i
        # Format { row: { columnKey: value } }
        self._options: Dict[int, Dict[str, str]] = dict()

    # def getOption(self, colKey: str, row: int) -> Optional[str]:
    #     qIndex = self.index(row, self._inverseOptionsPos[colKey], QModelIndex())
    #     return self.data(qIndex, Qt.DisplayRole)
    #
    # def setOption(self, colKey: str, row: int, value: str) -> None:
    #     qIndex = self.index(row, self._inverseOptionsPos[colKey], QModelIndex())
    #     self.setData(qIndex, value, Qt.EditRole)

    def validatorColumn(self, column: int) -> Optional[QValidator]:
        # If column is not an option then no validator
        if column not in self._optionsPos.keys():
            return None
        return self._optionsDesc[self._optionsPos[column]][1]

    def options(self) -> Dict[int, Dict[str, str]]:
        selectedRows = self.checkedAttributes
        opt = {k: self._options.get(k, dict()) for k in selectedRows}
        return opt

    def setOptions(self, opt: Dict[int, Dict[str, str]]) -> None:
        self._options = copy.deepcopy(opt)
        self.checkedAttributes = list(self._options.keys())

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        base = super().columnCount()
        nOptions = len(self._optionsDesc)
        return base + nOptions

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        # Handle option columns
        if (role == Qt.DisplayRole or role == Qt.EditRole) and index.column() in self._optionsPos.keys():
            rowOptions = self._options.get(index.row(), None)
            if rowOptions and index.row() in self.checkedAttributes:
                option = rowOptions.get(self._optionsPos[index.column()], None)
                if option:
                    return option
            return None
        # Everything else is handled by superclass
        return super().data(index, role)

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if not index.isValid():
            return False

        # Change option name
        if role == Qt.EditRole:
            if index.column() in self._optionsPos.keys():
                if self.data(index, Qt.DisplayRole) != value:
                    optionsForRow = self._options.get(index.row(), dict())
                    entry = {self._optionsPos[index.column()]: value}
                    optionsForRow.update(entry)
                    self._options[index.row()] = optionsForRow
                    self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                    return True
                return False
            elif index.column() == self.checkboxColumn:
                changed = super().setData(index, value, role)
                if changed:
                    for optionIndex in self._optionsPos.keys():
                        qi = self.index(index.row(), optionIndex, QModelIndex())
                        self.dataChanged.emit(qi, qi, [Qt.DisplayRole, Qt.EditRole])
                    return True
                return False
        return super().setData(index, value, role)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and \
                section in self._optionsPos.keys():
            return self._optionsDesc[self._optionsPos[section]][0]
        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        f = super().flags(index)
        if index.column() in self._optionsPos.keys() and index.row() in self.checkedAttributes:
            f |= Qt.ItemIsEditable
        return f


class OptionValidatorDelegate(QStyledItemDelegate):
    """ Delegate object used to set a QValidator for every option editor """

    def __init__(self, validator, parent=None):
        super().__init__(parent)
        self.__validator: QValidator = validator

    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget:
        editor = QLineEdit(parent)
        self.__validator.setParent(parent)
        editor.setValidator(self.__validator)
        return editor


@singleton
class OptionsEditorFactory:
    def __init__(self):
        self.__body: QWidget = None
        self.__layout: QFormLayout = None
        self.__optionsGetter: Dict[str, Callable] = dict()
        self.__optionsSetter: Dict[str, Callable] = dict()
        self.__editorWidgets: List[Tuple[str, QWidget]] = list()

    def withAttributeTable(self, key: str, checkbox: bool, nameEditable: bool, showTypes: bool,
                           options: Dict[str, Tuple[str, QValidator]], types: List):
        tableWidget = SearchableAttributeTableWidget(self.__body)
        tableModel = AttributeTableWithOptions(self.__body, checkbox, nameEditable, showTypes, options)
        tableWidget.setAttributeModel(tableModel, filterTypes=types)
        # Set up validator for every option columns
        for col in range(tableModel.columnCount()):
            validator = tableModel.validatorColumn(col)
            if validator:
                tableWidget.tableView.setItemDelegateForColumn(col, OptionValidatorDelegate(validator,
                                                                                            tableWidget.tableView))
        self.__layout.addRow(tableWidget)
        self.__optionsGetter[key] = tableModel.options
        self.__optionsSetter[key] = tableModel.setOptions
        self.__editorWidgets.append((key, tableWidget))

    def withTextField(self, label: str, key: str, validator: QValidator = None) -> None:
        textEdit = QLineEdit(self.__body)
        if validator:
            validator.setParent(textEdit)
            textEdit.setValidator(validator)
        self.__layout.addRow(label, textEdit)
        self.__optionsGetter[key] = textEdit.text
        self.__optionsSetter[key] = textEdit.setText
        self.__editorWidgets.append((key, textEdit))

    def withCheckBox(self, label: str, key: str) -> None:
        checkbox = QCheckBox(label, self.__body)
        self.__layout.addRow(checkbox)
        self.__optionsGetter[key] = checkbox.isChecked
        self.__optionsSetter[key] = checkbox.setChecked
        self.__editorWidgets.append((key, checkbox))

    def withRadioGroup(self, label: str, key: str, values: List[Tuple[str, Any]]) -> None:
        group = RadioButtonGroup(label, self.__body)
        for v in values:
            group.addRadioButton(v[0], v[1], False)
        self.__layout.addRow(group.glayout)
        self.__optionsGetter[key] = group.getData
        self.__optionsSetter[key] = group.setData  # wants the value
        self.__editorWidgets.append((key, group))

    def initEditor(self) -> None:
        """
        Initializes an editor object clearing the internal state.
        You should call this method every time you need to generate a new editor.
        """

        self.__body = QWidget()
        self.__layout = QFormLayout(self.__body)
        self.__optionsGetter: Dict[str, Callable] = dict()
        self.__optionsSetter: Dict[str, Callable] = dict()
        self.__editorWidgets: List[Tuple[str, QWidget]] = list()
        self.__layout.setHorizontalSpacing(30)

    # def addComboBox(self, label: str, options: QAbstractItemModel, tooltip: str = '') -> None:
    #     row: int = self.__layout.rowCount()
    #     self.__layout.addWidget(QLabel(label), row, 0)
    #     combo = QComboBox()
    #     if tooltip: combo.setToolTip(tooltip)
    #     options.setParent(combo)
    #     combo.setModel(options)
    #     self.__layout.addWidget(combo, row, 1)
    #     self.__optionsGetter.append(combo.currentText)

    def getEditor(self) -> AbsOperationEditor:
        class Editor(AbsOperationEditor):
            def editorBody(self) -> QWidget:
                pass

            def getOptions(self) -> Iterable:
                pass

            def setOptions(self, *args, **kwargs) -> None:
                pass

        def getOptions() -> Dict:
            options = dict()
            for k, get in self.__optionsGetter.items():
                options[k] = get()
            return options

        def setOptions(*args, **kwargs) -> None:
            assert bool(kwargs)  # factory editors must use kwargs
            for k, v in kwargs.items():
                self.__optionsSetter[k](v)

        e = Editor()
        self.__body.setParent(e)
        e.editorBody = lambda: self.__body
        e.getOptions = getOptions
        e.setOptions = setOptions

        # Add widgets as fields in editor
        for key, w in self.__editorWidgets:
            setattr(e, key, w)

        e.setUpEditor()
        return e
