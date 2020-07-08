import copy
from typing import Dict, List, Callable, Tuple, Any, Iterable, Optional

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtGui import QValidator
from PySide2.QtWidgets import QLineEdit, QCheckBox, \
    QWidget, QFormLayout, QStyledItemDelegate, QAbstractItemDelegate

from data_preprocessor.decorators.generic import singleton
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from data_preprocessor.gui.editor.optionwidget import RadioButtonGroup
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, AttributeTableModel


class AttributeTableWithOptions(AttributeTableModel):
    def __init__(self, parent: QWidget = None, checkable: bool = False,
                 editable: bool = False, showTypes: bool = True,
                 options: Optional[
                     Dict[str, Tuple[str, Optional[QAbstractItemDelegate], Optional[Any]]]] = None):
        super().__init__(parent, checkable, editable, showTypes)
        # options description { key, (label, delegate, default_value) }
        self._optionsDesc: Dict[str, Tuple[
            str, Optional[QAbstractItemDelegate], Optional[Any]]] = options if options else dict()
        # Column position for each option column
        self._optionsPos: Dict[int, str] = dict()
        self._inverseOptionsPos: Dict[str, int] = dict()
        baseCount = super().columnCount()
        for i, opt in enumerate(self._optionsDesc.keys()):
            self._optionsPos[baseCount + i] = opt
            self._inverseOptionsPos[opt] = baseCount + i
        # Format { row: { columnKey: value } }
        self._options: Dict[int, Dict[str, Any]] = dict()

    def delegateForColumn(self, column: int) -> Optional[QAbstractItemDelegate]:
        # If column is not an option then no delegate
        if column not in self._optionsPos.keys():
            return None
        delegate: Optional[QAbstractItemDelegate] = self._optionsDesc[self._optionsPos[column]][1]
        if delegate:
            return delegate
        return None

    def defaultValueForColumn(self, column: int) -> Optional[Any]:
        # If column is not an option then no default value
        if column not in self._optionsPos.keys():
            return None
        return self._optionsDesc[self._optionsPos[column]][2]

    def options(self) -> Dict[int, Dict[str, Any]]:
        selectedRows = self.checked
        opt = {k: self._options.get(k, dict()) for k in selectedRows}
        return opt

    def setOptions(self, opt: Dict[int, Dict[str, Any]]) -> None:
        self._options = copy.deepcopy(opt)
        self.setChecked(list(self._options.keys()), True)

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
            if index.row() in self.checked:
                rowOptions = self._options.get(index.row(), None)
                if rowOptions:
                    # For selected column show the values set or a default value (if set)
                    option = rowOptions.get(self._optionsPos[index.column()], None)
                    if option is not None:
                        return option
                # No options are set for current checked row
                if role == Qt.DisplayRole:
                    # Only for DisplayRole, since in EditRole the correct value must be None
                    return self.defaultValueForColumn(index.column())
            return None
        # Everything else is handled by superclass
        return super().data(index, role)

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if not index.isValid():
            return False

        # Change option name
        if role == Qt.EditRole:
            if index.column() in self._optionsPos.keys():
                if self.data(index, Qt.EditRole) != value:
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
        if index.column() in self._optionsPos.keys() and index.row() in self.checked:
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
                           options: Optional[Dict[str, Tuple[str, Optional[QAbstractItemDelegate],
                                                             Optional[Any]]]],
                           types: Optional[List]):
        """
        Adds a table widget to the editor

        :param key: parameter name of the options for the table
        :param checkbox: whether to show a checkbox column in the table
        :param nameEditable: whether attribute name should be editable with double click
        :param showTypes: whether to show a column with the type of each attribute
        :param options: option specifier. Any entry in this dictionary will result in a new column in
            the table with header name specified as first argument in the tuple and an optional delegate
            object which will be used in the editor widget after a double click on the option cell.
            The third argument is an optional default value to show on selected rows where no options
            has been set
        :param types: the list of accepted types to show. If None no filter will be applied
        """
        tableWidget = SearchableAttributeTableWidget(self.__body)
        tableModel = AttributeTableWithOptions(self.__body, checkbox, nameEditable, showTypes, options)
        tableWidget.setAttributeModel(tableModel, filterTypes=types)
        # Set up validator for every option columns
        for col in range(tableModel.columnCount()):
            delegate = tableModel.delegateForColumn(col)
            if delegate:
                delegate.setParent(tableWidget.tableView)
                tableWidget.tableView.setItemDelegateForColumn(col, delegate)
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
