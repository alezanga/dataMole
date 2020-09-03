from enum import Enum, unique
from typing import List, Tuple, Iterable, Optional

import prettytable as pt
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget, QCheckBox, QVBoxLayout, QGroupBox, QGridLayout, QLabel

from dataMole import data, flogging
from dataMole import exceptions as exp
from dataMole.data.types import Types, Type, IndexType
from dataMole.gui.editor.interface import AbsOperationEditor
from dataMole.gui.utils import AttributeComboBox, TextOptionWidget, RadioButtonGroup
from .interface.graph import GraphOperation


class Join(GraphOperation, flogging.Loggable):
    @unique
    class JoinType(Enum):
        Left = 'left'
        Right = 'right'
        Inner = 'inner'
        Outer = 'outer'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__lSuffix: str = '_l'
        self.__rSuffix: str = '_r'
        self.__onIndex: bool = True
        self.__leftOn: int = None
        self.__rightOn: int = None
        self.__type: Join.JoinType = Join.JoinType.Left

    def logOptions(self) -> str:
        tt = pt.PrettyTable(field_names=['Option', 'Value'], print_empty=False)
        tt.align = 'l'
        tt.add_row(['Join type', self.__type.value])
        tt.add_row(['By index', self.__onIndex])
        tt.add_row(['Left column', self.__leftOn if not self.__onIndex else '-'])
        tt.add_row(['Right column', self.__rightOn if not self.__onIndex else '-'])
        tt.add_row(['Suffix left', self.__lSuffix])
        tt.add_row(['Suffix right', self.__rSuffix])
        return tt.get_string(vrules=pt.ALL, border=True)

    def execute(self, dfl: data.Frame, dfr: data.Frame) -> data.Frame:
        if self.__onIndex:
            # Join on indexes
            return data.Frame(dfl.getRawFrame().join(dfr.getRawFrame(), how=self.__type.value,
                                                     lsuffix=self.__lSuffix,
                                                     rsuffix=self.__rSuffix))
        else:
            # Join (merge) on columns
            # onleft and onright must be set
            suffixes = (self.__lSuffix, self.__rSuffix)
            l_col = dfl.shape.colNames[self.__leftOn]
            r_col = dfr.shape.colNames[self.__rightOn]
            return data.Frame(dfl.getRawFrame().merge(dfr.getRawFrame(), how=self.__type.value,
                                                      left_on=l_col,
                                                      right_on=r_col,
                                                      suffixes=suffixes))

    @staticmethod
    def name() -> str:
        return 'Join'

    @staticmethod
    def shortDescription() -> str:
        return 'Join two tables on indexes or columns. Supports left, right, outer and inner join'

    def acceptedTypes(self) -> List[Type]:
        return [Types.Numeric, Types.Ordinal, Types.Nominal, Types.String]

    def setOptions(self, ls: str, rs: str, onindex: bool, onleft: int, onright: int,
                   joinType: JoinType) -> None:
        errors = list()
        ls = ls.strip()
        rs = rs.strip()
        if not ls or not rs:
            errors.append(('suffix', 'Error: both suffixes are required'))
        elif ls == rs:
            errors.append(('suffixequals', 'Error: suffixes must be different'))
        if not joinType:
            errors.append(('jointype', 'Error: join type is not set'))
        # if not all(self.shapes):
        #     errors.append(('shape', 'Error: some input is missing. Connect all source inputs before '
        #                             'setting options'))
        if all(self.shapes):
            if onindex:
                # Check index types
                if not self.shapes[0].index or not self.shapes[1].index:
                    errors.append(('index', 'Error: join on indices require both indices to be set'))
                else:
                    llen = self.shapes[0].nIndexLevels
                    rlen = self.shapes[1].nIndexLevels
                    if llen == rlen == 1:
                        # Single index join
                        tl = self.shapes[0].indexTypes[0]
                        tr = self.shapes[1].indexTypes[0]
                        if not self._checkColumnTypes(tl, tr):
                            errors.append(('type', 'Error: type "{}" and "{}" are not '
                                                   'compatible'.format(tl.name, tr.name)))
                    else:
                        # Multiindex join, check that name intersection in compatible
                        indexNamesL = set(self.shapes[0].index)
                        indexNamesR = set(self.shapes[1].index)
                        indexDictL = self.shapes[0].indexDict
                        indexDictR = self.shapes[1].indexDict
                        for name in indexNamesL:
                            if name in indexNamesR:
                                tl = indexDictL[name]
                                tr = indexDictR[name]
                                if not self._checkColumnTypes(tl, tr):
                                    errors.append(('type', 'Error: common index level "{}" has '
                                                           'different types "{}" and "{}" which are not '
                                                           'compatible'.format(name, tl.name, tr.name)))
                                    break
            else:
                # Merge on columns: check types
                tl: Type = self.shapes[0].colTypes[onleft]
                tr: Type = self.shapes[1].colTypes[onright]
                if not self._checkColumnTypes(tl, tr):
                    errors.append(('type', 'Error: column types "{}" and "{}" are not compatible'
                                   .format(tl.name, tr.name)))
        if errors:
            raise exp.OptionValidationError(errors)

        self.__lSuffix = ls
        self.__rSuffix = rs
        self.__onIndex = onindex
        self.__leftOn = onleft
        self.__rightOn = onright
        self.__type = joinType

    @staticmethod
    def _checkColumnTypes(lt: Type, rt: Type) -> bool:
        if isinstance(lt, IndexType) and isinstance(rt, IndexType):
            lt = lt.type
            rt = rt.type
        return lt == rt or {lt, rt} <= {Types.String, Types.Ordinal, Types.Nominal}

    def unsetOptions(self) -> None:
        self.__leftOn: int = None
        self.__rightOn: int = None

    def getOptions(self) -> Tuple[str, str, bool, int, int, JoinType]:
        return self.__lSuffix, self.__rSuffix, self.__onIndex, self.__leftOn, self.__rightOn, self.__type

    def getEditor(self) -> AbsOperationEditor:
        return _JoinEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.refresh()

    def hasOptions(self) -> bool:
        modeOk = self.__onIndex is True or (self.__leftOn is not None and self.__rightOn is not None)
        return self.__lSuffix and self.__rSuffix and modeOk and self.__type in Join.JoinType

    def needsOptions(self) -> bool:
        return True

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


export = Join


class _JoinEditor(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        self.__g = RadioButtonGroup('Select join type:', self)
        for j in Join.JoinType:
            self.__g.addRadioButton(j.name, j, False)

        self.__onIndex = QCheckBox('Join on index?', self)

        self.__jpl = _JoinPanel('Left', None, None, self)
        self.__jpr = _JoinPanel('Right', None, None, self)

        w = QWidget(self)
        self.layout = QGridLayout()
        self.layout.addLayout(self.__g.glayout, 0, 0, 1, -1)
        self.layout.addWidget(self.__onIndex, 1, 0, 1, -1)
        self.layout.addWidget(self.__jpl, 2, 0, 1, 1)
        self.layout.addWidget(self.__jpr, 2, 1, 1, 1)
        self.errorLabel = QLabel(self)
        self.errorLabel.setWordWrap(True)
        self.layout.addWidget(self.errorLabel, 3, 0, 1, -1)
        self.layout.setHorizontalSpacing(15)
        self.layout.setVerticalSpacing(10)
        w.setLayout(self.layout)

        # Clear errors when something change
        self.__onIndex.stateChanged.connect(self.__onStateChange)
        self.__onIndex.stateChanged.connect(self.errorLabel.hide)

        return w

    def refresh(self) -> None:
        oldl = self.__jpl
        oldr = self.__jpr
        self.__jpl = _JoinPanel('Left', self.inputShapes[0], self.acceptedTypes, self)
        self.__jpr = _JoinPanel('Right', self.inputShapes[1], self.acceptedTypes, self)
        self.layout.replaceWidget(oldl, self.__jpl)
        self.layout.replaceWidget(oldr, self.__jpr)
        # Delete old widgets
        oldl.deleteLater()
        oldr.deleteLater()
        # Reconnect
        self.__jpl.box.widget.currentIndexChanged.connect(self.errorLabel.hide)
        self.__jpl.suffix.widget.textEdited.connect(self.errorLabel.hide)
        self.__jpr.box.widget.currentIndexChanged.connect(self.errorLabel.hide)
        self.__jpr.suffix.widget.textEdited.connect(self.errorLabel.hide)

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
                   type: Join.JoinType) -> None:
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
    def __init__(self, title: str, shape: data.Shape, types: List[Type], parent=None):
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
