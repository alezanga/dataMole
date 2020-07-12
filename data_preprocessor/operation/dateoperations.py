from typing import Iterable, List, Tuple, Optional

import pandas as pd
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QDateEdit, QTimeEdit, QCheckBox, QButtonGroup, QGridLayout, \
    QSpacerItem

from data_preprocessor import data
from data_preprocessor.data.types import Types, Type
from data_preprocessor.gui.editor import AbsOperationEditor
from data_preprocessor import exceptions as exp
from data_preprocessor.operation.interface.graph import GraphOperation


class DateDiscretizer(GraphOperation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attribute: int = None
        self.__intervals: List[pd.Interval] = list()
        self.__labels: List[str] = list()
        self.__byTime: bool = False
        self.__byDate: bool = True

    def execute(self, df: data.Frame) -> data.Frame:
        df = df.getRawFrame().copy(True)
        if not self.__byDate:
            raise NotImplementedError('Selection by time only is not implemented')
        if not self.__byTime:
            self.__intervals = list(map(
                lambda x: pd.Interval(pd.Timestamp(x.left.date()), pd.Timestamp(x.right.date())),
                self.__intervals))

        intervalIndex = pd.IntervalIndex(self.__intervals)
        df.iloc[:, self.__attribute] = pd.cut(df.iloc[:, self.__attribute], bins=intervalIndex)

        # Rename categories as specified with labels
        nameMap = {interval: lab for interval, lab in zip(df.iloc[:,
                                                          self.__attribute].cat.categories.to_list(),
                                                          self.__labels)}
        df.iloc[:, self.__attribute].cat.rename_categories(nameMap, inplace=True)

        return data.Frame(df)

    @staticmethod
    def name() -> str:
        return 'Date discretizer'

    def shortDescription(self) -> str:
        return 'Discretize date and times based on ranges'

    def acceptedTypes(self) -> List[Type]:
        return [Types.Datetime]

    def hasOptions(self) -> bool:
        return self.__intervals is not None and self.__attribute is not None and self.__labels

    def unsetOptions(self) -> None:
        self.__attribute = None

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        options: List[Tuple[pd.Interval, str]] = list()
        if self.__intervals:
            options = list(zip(self.__intervals, self.__labels))
        return self.__attribute, options, self.__byDate, self.__byTime

    def setOptions(self, attribute: Optional[int], intervals: List[Tuple[pd.Interval, str]],
                   byDate: bool, byTime: bool) -> None:
        intervalList = list(map(lambda x: x[0], intervals))
        intervalIndex = pd.IntervalIndex(intervalList)
        labels: List[str] = list(map(lambda x: x[1].strip() if x[1] else None, intervals))

        errors = list()
        if attribute is None:
            errors.append(('attribute', 'Error: target attribute is not selected'))
        if intervalIndex.is_overlapping:
            errors.append(('overlapping', 'Error: intervals are overlapping'))
        if not all(labels):
            errors.append(('labels', 'Error: name is not set in every interval'))
        if errors:
            raise exp.OptionValidationError(errors)

        self.__attribute = attribute
        self.__intervals = intervalList
        self.__labels = labels
        self.__byDate = byDate
        self.__byTime = byTime

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions() or not self.shapes[0]:
            return None
        s = self.shapes[0].clone()
        s.colTypes[self.__attribute] = Types.Ordinal
        return s

    def getEditor(self) -> AbsOperationEditor:
        pass

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


class _DateDiscretizerEditor(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        pass

    def getOptions(self) -> Iterable:
        pass

    def setOptions(self, *args, **kwargs) -> None:
        pass


class _BodyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Checkboxes
        self.byTime = QCheckBox('By time', self)
        self.byDate = QCheckBox('By date', self)
        self.buttonGroup = QButtonGroup(self)
        self.buttonGroup.addButton(self.byDate)
        self.buttonGroup.addButton(self.byTime)
        self.__checkedCount: int = 0
        self.buttonGroup.buttonToggled.connect(self.checkboxToggled)

    @Slot(QCheckBox, bool)
    def checkboxToggled(self, button: QCheckBox, checked: bool) -> None:
        if checked is True:
            self.__checkedCount += 1
        elif self.__checkedCount == 1:
            # Don't allow to have no button checked
            button.setChecked(True)

        if button is self.byTime:
            # update layout
            pass


class _IntervalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dateStartCB = QDateEdit(self)
        self.dateEndCB = QDateEdit(self)
        self.timeStartCB = QTimeEdit(self)
        self.timeEndCB = QTimeEdit(self)

        self.gLayout = QGridLayout(self)
        self.gLayout.addWidget(QDateEdit(self), 1, 0)
        self.gLayout.addWidget(QDateEdit(self), 1, 1)
        self.gLayout.addItem(QSpacerItem(50, 0), 1, 2)
        self.gLayout.addWidget(QTimeEdit(self), 1, 3)
        self.gLayout.addWidget(QTimeEdit(self), 1, 4)

    def addTime(self) -> None:
        for row in range(self.gLayout.rowCount()):
            self.gLayout.addItem(QSpacerItem(50, 0), row, 2)
            self.gLayout.addWidget(QTimeEdit(), row, 3)
            self.gLayout.addWidget(QTimeEdit(), row, 4)

    def removeTime(self) -> None:
        for row in range(self.gLayout.rowCount()):
            self.gLayout.removeItem(self.gLayout.itemAtPosition(row, 2))
            self.gLayout.itemAtPosition(row, 3).widget().deleteLater()
            self.gLayout.itemAtPosition(row, 4).widget().deleteLater()

    def addDate(self) -> None:
        for row in range(self.gLayout.rowCount()):
            self.gLayout.addWidget(QDateEdit(), row, 0)
            self.gLayout.addWidget(QDateEdit(), row, 1)
            self.gLayout.addItem(QSpacerItem(50, 0), row, 2)

    def removeDate(self) -> None:
        for row in range(self.gLayout.rowCount()):
            self.gLayout.removeItem(self.gLayout.itemAtPosition(row, 2))
            self.gLayout.itemAtPosition(row, 0).widget().deleteLater()
            self.gLayout.itemAtPosition(row, 1).widget().deleteLater()

    def addRow(self) -> None:
        pass

    def removeRow(self) -> None:
        pass
