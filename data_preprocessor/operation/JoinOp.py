from enum import Enum, unique
from typing import List, Tuple, Iterable, Optional

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget, QCheckBox, QVBoxLayout, QGroupBox, QGridLayout, QLabel

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.exceptions import OptionValidationError
from .interface.graph import GraphOperation
from ..gui.editor.optionwidget import AttributeComboBox, TextOptionWidget, RadioButtonGroup


@unique
class JoinType(Enum):
    Left = 'left'
    Right = 'right'
    Inner = 'inner'
    Outer = 'outer'


jt = JoinType


class JoinOp(GraphOperation):
    def __init__(self):
        super().__init__()
        self.__lsuffix: str = '_l'
        self.__rsuffix: str = '_r'
        self.__on_index: bool = True
        self.__left_on: int = None
        self.__right_on: int = None
        self.__type: JoinType = jt.Left

    def execute(self, dfl: data.Frame, dfr: data.Frame) -> data.Frame:
        # sr = dfr.shape
        # sl = dfl.shape
        if self.__on_index:
            return data.Frame(dfl.getRawFrame().join(dfr.getRawFrame(), how=self.__type.value,
                                                     lsuffix=self.__lsuffix,
                                                     rsuffix=self.__rsuffix))
        else:
            # onleft and onright must be set
            suffixes = (self.__lsuffix, self.__rsuffix)
            l_col = dfl.shape.col_names[self.__left_on]
            r_col = dfl.shape.col_names[self.__right_on]
            return data.Frame(dfl.getRawFrame().merge(dfr.getRawFrame(), how=self.__type.value,
                                                      left_on=l_col,
                                                      right_on=r_col,
                                                      suffixes=suffixes))

    @staticmethod
    def name() -> str:
        return 'Join operation'

    def shortDescription(self) -> str:
        return 'Allows to join two tables. Can handle four type of join: left, right, outer and inner'

    def acceptedTypes(self) -> List[Types]:
        return [Types.Numeric, Types.Categorical, Types.String]

    def setOptions(self, ls: str, rs: str, onindex: bool, onleft: int, onright: int,
                   join_type: JoinType) -> None:
        errors = list()
        if not ls or not rs:
            errors.append(('suffix', 'Error: suffixes are required'))
        if onindex and all(self.shapes) and \
                (not self.shapes[0].index or not self.shapes[1].index):
            errors.append(('index', 'Error: join on indices require both indices to be set'))
        if not onindex and all(self.shapes):
            type_l = self.shapes[0].col_types[onleft]
            type_r = self.shapes[1].col_types[onright]
            if type_l != type_r:
                errors.append(('type_mismatch',
                               'Error: column types must match. Instead got \'{}\' and \'{}\''
                               .format(type_l.name, type_r.name)))
        if errors:
            raise OptionValidationError(errors)

        self.__lsuffix = ls
        self.__rsuffix = rs
        self.__on_index = onindex
        self.__left_on = onleft
        self.__right_on = onright
        self.__type = join_type

    def unsetOptions(self) -> None:
        self.__left_on: int = None
        self.__right_on: int = None

    def getOptions(self) -> Tuple[str, str, bool, int, int, JoinType]:
        return (self.__lsuffix, self.__rsuffix, self.__on_index, self.__left_on, self.__right_on,
                self.__type)

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        # TODO: editor here must ensure types of selected columns match
        return _JoinEditor()

    def hasOptions(self) -> bool:
        on = self.__on_index is True or (self.__left_on is not None and self.__right_on is not None)
        return self.__lsuffix and self.__rsuffix and on and self.__type in JoinType

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    @staticmethod
    def minInputNumber() -> int:
        return 2

    @staticmethod
    def maxInputNumber() -> int:
        return 2

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1


export = JoinOp


class _JoinEditor(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        self.__g = RadioButtonGroup('Select join type:', self)
        for j in JoinType:
            self.__g.addRadioButton(j.name, j, False)

        self.__onIndex = QCheckBox('Join on index?', self)

        self.__jpl = _JoinPanel('Left', self.inputShapes[0], self.acceptedTypes, self)
        self.__jpr = _JoinPanel('Right', self.inputShapes[1], self.acceptedTypes, self)

        w = QWidget(self)
        layout = QGridLayout(w)
        layout.addLayout(self.__g.glayout, 0, 0, 1, -1)
        layout.addWidget(self.__onIndex, 1, 0, 1, -1)
        layout.addWidget(self.__jpl, 2, 0, 1, 1)
        layout.addWidget(self.__jpr, 2, 1, 1, 1)
        self.errorLabel = QLabel(self)
        self.errorLabel.setWordWrap(True)
        layout.addWidget(self.errorLabel, 3, 0, 1, -1)
        layout.setHorizontalSpacing(15)
        layout.setVerticalSpacing(10)
        w.setLayout(layout)

        # Clear errors when something change
        self.__onIndex.stateChanged.connect(self.__onStateChange)
        self.__onIndex.stateChanged.connect(self.errorLabel.hide)
        self.__jpl.box.widget.currentIndexChanged.connect(self.errorLabel.hide)
        self.__jpl.suffix.widget.textEdited.connect(self.errorLabel.hide)
        self.__jpr.box.widget.currentIndexChanged.connect(self.errorLabel.hide)
        self.__jpr.suffix.widget.textEdited.connect(self.errorLabel.hide)

        return w

    def showErrors(self, msg: str) -> None:
        text = self.errorLabel.text()
        if text:
            text += '<br>' + msg
        self.errorLabel.setText(text)

    def getOptions(self) -> Iterable:
        attrL, suffL = self.__jpl.getData()
        attrR, suffR = self.__jpr.getData()
        jtype = self.__g.getData()
        onIndex = self.__onIndex.isChecked()
        return suffL, suffR, onIndex, attrL, attrR, jtype

    def setOptions(self, lsuffix: str, rsuffix: str, on_index: bool, left_on: int, right_on: int,
                   type: JoinType) -> None:
        self.__jpl.setData(left_on, lsuffix)
        self.__jpr.setData(right_on, rsuffix)
        self.__onIndex.setChecked(on_index)
        self.__g.setData(type)

    @Slot(Qt.CheckState)
    def __onStateChange(self, state: Qt.CheckState) -> None:
        if state == Qt.Checked:
            self.__jpl.box.widget.setDisabled(True)
            self.__jpr.box.widget.setDisabled(True)
        else:
            self.__jpl.box.widget.setEnabled(True)
            self.__jpr.box.widget.setEnabled(True)


class _JoinPanel(QGroupBox):
    def __init__(self, title: str, shape: data.Shape, types: List[Types], parent=None):
        super().__init__(title, parent)
        self.box = AttributeComboBox(shape, types, 'Select the attribute', self)
        self.suffix = TextOptionWidget('Suffix', self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.box)
        layout.addWidget(self.suffix)

    def getData(self) -> Tuple[Optional[int], str]:
        return self.box.getData(), self.suffix.getData()

    def setData(self, index: Optional[int], text: str) -> None:
        self.box.setData(index)
        self.suffix.setData(text)
