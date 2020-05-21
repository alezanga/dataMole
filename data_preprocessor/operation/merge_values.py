from typing import Iterable, List, Any, Tuple

import numpy as np
from PySide2.QtCore import Qt, Slot, QRegExp
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import QWidget, QCheckBox, QHBoxLayout, QVBoxLayout, QLabel

import data_preprocessor.gui.editor.optionwidget as opw
from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.graph import GraphOperation


class MergeValuesOp(GraphOperation):
    """ Merge values of one attribute into a single value """
    Nan = np.nan

    def __init__(self):
        super().__init__()
        self.__attribute: int = None
        self.__values_to_merge: List = list()
        self.__merge_val: Any = None

    def execute(self, df: data.Frame) -> data.Frame:
        # Check if type of attribute is accepted
        if df.shape.col_types[self.__attribute] not in self.acceptedTypes():
            return df
        # If type is accepted proceed
        pd_df = df.getRawFrame().copy()
        pd_df.iloc[:, [self.__attribute]] = pd_df.iloc[:, [self.__attribute]] \
            .replace(to_replace=self.__values_to_merge, value=self.__merge_val, inplace=False)
        return data.Frame(pd_df)

    @staticmethod
    def name() -> str:
        return 'Merge values'

    def shortDescription(self) -> str:
        return 'Substitute all specified values in a attribute and substitute them with a single value'

    def acceptedTypes(self) -> List[Types]:
        return [Types.String, Types.Categorical, Types.Numeric]

    def setOptions(self, attribute: int, values_to_merge: List, value: Any) -> None:
        attribute, values_to_merge, value = self.validateConvertOptions(attribute, values_to_merge,
                                                                        value)
        self.__attribute = attribute
        self.__values_to_merge = values_to_merge
        self.__merge_val = value  # could be Nan

    def unsetOptions(self) -> None:
        self.__attribute = None
        self.__values_to_merge = list()
        self.__merge_val = None

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return self.__attribute, self.__values_to_merge, self.__merge_val

    def getEditor(self) -> AbsOperationEditor:
        return _MergeValEditor()

    def hasOptions(self) -> bool:
        return self.__attribute and self.__values_to_merge and self.__merge_val

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    @staticmethod
    def minInputNumber() -> int:
        return 1

    @staticmethod
    def maxInputNumber() -> int:
        return 1

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1

    def validateConvertOptions(self, attribute: int, values_to_merge: List, value: Any) -> Tuple:
        def any_not_float(values: List):
            for v in values:
                try:
                    float(v)
                except ValueError:
                    return True
            return False

        errors = list()
        if attribute is not None and self._shape[0].col_types[attribute] == Types.Numeric:
            if any_not_float(values_to_merge):
                errors.append(
                    ('mergelist', 'You selected a numeric attribute, but merge values include non '
                                  'numeric values'))
            else:
                values_to_merge = list(map(float, values_to_merge))
            if value is not None:
                if any_not_float([value]):
                    errors.append(
                        ('mergevalue', 'You selected a numeric attribute but the value to replace '
                                       'is non numeric'))
                else:
                    value = float(value)
        if errors:
            raise OptionValidationError(errors)
        else:
            return attribute, values_to_merge, value


class _MergeValEditor(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        self.setWindowTitle('Merge values')
        self.__attributeComboBox = opw.AttributeComboBox(self.inputShapes[0], self.acceptedTypes,
                                                         'Select an attribute')
        self.__mergeList = opw.TextOptionWidget('Add values to replace (separated by comma)')
        self.__mergeValue = opw.TextOptionWidget()
        self.__nan_cb = QCheckBox()
        self.__curr_type = None
        self.__nan_cb.setText('to Nan')
        layoutH = QHBoxLayout()
        layoutH.addWidget(self.__mergeValue)
        layoutH.addWidget(self.__nan_cb)

        layout = QVBoxLayout()
        layout.addWidget(self.__attributeComboBox)
        layout.addWidget(self.__mergeList)
        layout.addWidget(QLabel('Substitute value'))
        layout.addLayout(layoutH)

        self.__nan_cb.stateChanged.connect(self.toggleValueEdit)
        self.__attributeComboBox.widget.currentIndexChanged[int].connect(self.toggleValidator)
        self.__mergeList.widget.textEdited.connect(self.clearError)
        self.__mergeValue.widget.textEdited.connect(self.clearError)
        self.__attributeComboBox.widget.currentIndexChanged[str].connect(self.clearError)
        self.__nan_cb.stateChanged.connect(self.clearError)

        self.errorHandlers['mergelist'] = self.__mergeList.setError
        self.errorHandlers['mergevalue'] = self.__mergeValue.setError
        body = QWidget(self)
        body.setLayout(layout)
        return body

    @Slot(int)
    def toggleValueEdit(self, state: Qt.CheckState) -> None:
        if state == Qt.Checked:
            self.__mergeValue.widget.setDisabled(True)
        else:
            self.__mergeValue.widget.setDisabled(False)

    @Slot(int)
    def toggleValidator(self, index: int) -> None:
        prev_type = self.__curr_type
        self.__curr_type = self.inputShapes[0].col_types[index]
        if self.__curr_type != prev_type:
            if self.__curr_type == Types.Numeric:
                reg = QRegExp('(\\d+(\\.\\d)?\\d*)(\\,\\s?(\\d+(\\.\\d)?\\d*))*')
            else:
                reg = QRegExp('((\\S+)|(\'.+\'))(,\\s?((\\S+)|(\'.+\')))*')
            b = self.__mergeList.widget.validator()
            self.__mergeList.widget.setValidator(QRegExpValidator(reg, self))
            text = self.__mergeList.widget.text()
            if self.__mergeList.widget.validator().validate(text, len(text) - 1)[0] == \
                    QRegExpValidator.Invalid:
                self.__mergeList.widget.setText('')
                self.__mergeList.unsetError()
            if b:
                b.deleteLater()

    def getOptions(self) -> Iterable:
        cur_attr = self.__attributeComboBox.getData()
        list_merge = self.__mergeList.getData()
        list_merge = [s.strip() for s in list_merge.strip(',').strip().split(',')] if list_merge else \
            list()
        vv = self.__mergeValue
        if self.__nan_cb.isChecked():
            value = MergeValuesOp.Nan
        else:
            value = vv.getData()
        return cur_attr, list_merge, value

    def setOptions(self, attribute: int, values_to_merge: List, merge_val: Any) -> None:
        if values_to_merge:
            self.__mergeList.setData(', '.join([str(e) for e in values_to_merge]))
        if merge_val is not None:
            if merge_val is MergeValuesOp.Nan:
                self.__nan_cb.setChecked(True)
                self.__nan_cb.stateChanged.emit(self.__nan_cb.checkState())
            else:
                self.__mergeValue.setData(str(merge_val))
        self.__attributeComboBox.setData(attribute)
        if attribute is not None:
            self.toggleValidator(attribute)
            self.__curr_type = self.inputShapes[0].col_types[attribute]

    @Slot(str)
    def clearError(self, _):
        self.__mergeList.unsetError()
        self.__mergeValue.unsetError()
        self.__attributeComboBox.unsetError()


export = MergeValuesOp
