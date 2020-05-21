from typing import Iterable, Union

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget, QButtonGroup, QLabel, QRadioButton, QSlider, QVBoxLayout, \
    QHBoxLayout, QSpinBox

from data_preprocessor import data
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.operation.interface.exceptions import InvalidOptions
from data_preprocessor.operation.interface.graph import GraphOperation


class RemoveNanRows(GraphOperation):
    def __init__(self):
        super().__init__()
        # range [0.0, 1.0]
        self.__thresholdPercentage: float = None
        # range [0, attribute number]
        self.__thresholdNumber: int = None

    def execute(self, df: data.Frame) -> data.Frame:
        # Assume everything to go is set
        if self.__thresholdPercentage is not None and self.__thresholdNumber is not None:
            raise InvalidOptions('Can\'t have both threshold set')
        pf = df.getRawFrame().copy()
        if self.__thresholdPercentage:
            # By percentage
            pf = pf.loc[pf.isnull().mean(axis=1) <= self.__thresholdPercentage]
        else:
            # By nan number
            pf = pf.loc[pf.isnull().sum(axis=1) <= self.__thresholdNumber]
        return data.Frame(pf)

    @staticmethod
    def name() -> str:
        return 'Remove nan rows'

    def shortDescription(self) -> str:
        return 'Remove all rows with a specified number or percentage of nan values'

    def longDescription(self) -> str:
        return 'Can operate in two modes: <ul>' \
               '<li>By removing rows with more than a minimum number of nan values </li>' \
               '<li>By removing rows with more than a ratio of nana values over all the attributes' \
               '</li>' \
               '</ul> Only one modality may be chosen'

    def hasOptions(self) -> bool:
        return (self.__thresholdPercentage is not None) ^ (self.__thresholdNumber is not None)

    def setOptions(self, percentage: float, number: int) -> None:
        if percentage is not None:
            self.__thresholdPercentage = percentage
            self.__thresholdNumber = None
        else:
            self.__thresholdPercentage = None
            self.__thresholdNumber = number

    def unsetOptions(self) -> None:
        # By number depends on input shape
        self.__thresholdNumber = None

    def getOutputShape(self) -> Union[data.Shape, None]:
        return self._shape[0]

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return self.__thresholdPercentage, self.__thresholdNumber

    def getEditor(self) -> AbsOperationEditor:
        return _RemoveNanEditor('row')

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


class RemoveNanColumns(GraphOperation):
    def __init__(self):
        super().__init__()
        # range [0.0, 1.0]
        self.__thresholdPercentage: float = None
        # range [0, attribute number]
        self.__thresholdNumber: int = None

    def execute(self, df: data.Frame) -> data.Frame:
        # Assume everything to go is set
        if self.__thresholdPercentage is not None and self.__thresholdNumber is not None:
            raise InvalidOptions('Can\'t have both threshold set')
        pf = df.getRawFrame().copy()
        if self.__thresholdPercentage:
            # By percentage
            pf = pf.loc[:, pf.isnull().mean() <= self.__thresholdPercentage]
        else:
            # By nan number
            pf = pf.loc[:, pf.isnull().sum() <= self.__thresholdNumber]
        return data.Frame(pf)

    @staticmethod
    def name() -> str:
        return 'Remove nan columns'

    def shortDescription(self) -> str:
        return 'Remove all columns with a specified number or percentage of nan values'

    def hasOptions(self) -> bool:
        return (self.__thresholdPercentage is not None) ^ (self.__thresholdNumber is not None)

    def setOptions(self, percentage: float, number: int) -> None:
        if percentage is not None:
            self.__thresholdPercentage = percentage
            self.__thresholdNumber = None
        else:
            self.__thresholdPercentage = None
            self.__thresholdNumber = number

    def unsetOptions(self) -> None:
        pass

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return self.__thresholdPercentage, self.__thresholdNumber

    def getEditor(self) -> AbsOperationEditor:
        return _RemoveNanEditor('col')

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return False

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


export = [RemoveNanRows, RemoveNanColumns]


class _RemoveNanEditor(AbsOperationEditor):
    _baseText = {
        0: 'Remove with more than: <b>{}</b> nan',
        1: 'Remove with more than: <b>{}%</b> nan'
    }

    def __init__(self, mode: str, parent: QWidget = None):
        """ Builds the editor

        :param mode: one of 'col' or 'row'
        :param parent: a parent widget
        """
        self.__mode: str = mode
        super().__init__(parent)

    def editorBody(self) -> QWidget:
        self.__group = QButtonGroup()
        self.__group.setExclusive(True)
        lab = QLabel('Choose how to remove:')
        self.__group.addButton(QRadioButton('By number'), id=0)
        self.__group.addButton(QRadioButton('By percentage'), id=1)
        self.__currId = None

        self.__sliderLabel = QLabel()
        self.__slider = QSlider(Qt.Horizontal, self)
        self.__slider.setMinimum(0)
        self.__slider.setTracking(True)
        self.__slider.setSingleStep(1)

        self.__numBox = QSpinBox()
        self.__numBox.setMinimum(0)
        self.__numBox.setMaximum(10000000)

        radioLayout = QHBoxLayout()
        radioLayout.addWidget(self.__group.button(0))
        radioLayout.addWidget(self.__group.button(1))
        self.__bodyLayout = QVBoxLayout()
        self.__bodyLayout.addWidget(lab)
        self.__bodyLayout.addLayout(radioLayout)
        self.__bodyLayout.addSpacing(20)
        self.__bodyLayout.addWidget(QLabel('Move the slider to set removal parameter:'))
        self.__bodyLayout.addSpacing(10)
        self.__bodyLayout.addWidget(self.__slider if self.__mode == 'row' else self.__numBox)
        self.__bodyLayout.addWidget(self.__sliderLabel)

        self.__group.buttonClicked[int].connect(self._toggleMode)
        # Both are connected, only one is shown
        self.__slider.valueChanged.connect(self._onValueChanged)
        self.__numBox.valueChanged[int].connect(self._onValueChanged)
        # Set a default button and label text
        self.__group.button(0).click()
        self.__sliderLabel.setText(self._baseText[0].format(self.__slider.minimum()))

        body = QWidget()
        body.setLayout(self.__bodyLayout)
        return body

    @Slot(int)
    def _toggleMode(self, bid: int) -> None:
        # NOTE: could be refactored
        if bid == self.__currId:
            return
        self.__currId = bid
        if bid == 0:
            if not self.inputShapes[0] and self.__mode == 'row':
                self.__slider.setDisabled(True)
                self._onValueChanged(self.__slider.value())
            elif not self.__slider.isEnabled():
                self.__slider.setEnabled(True)
            else:
                if self.__mode == 'row':
                    self.__slider.setMaximum(self.inputShapes[0].n_columns)
                    self._onValueChanged(self.__slider.value())
                else:
                    self.__bodyLayout.replaceWidget(self.__slider, self.__numBox)
                    self.__slider.hide()
                    self.__numBox.show()
                    self._onValueChanged(self.__numBox.value())
        else:
            if self.__mode == 'row':
                if not self.__slider.isEnabled():
                    self.__slider.setEnabled(True)
            else:
                self.__bodyLayout.replaceWidget(self.__numBox, self.__slider)
                self.__numBox.hide()
                self.__slider.show()
            self._onValueChanged(self.__slider.value())
            self.__slider.setMaximum(100)

    @Slot(int)
    def _onValueChanged(self, value: int):
        self.__sliderLabel.setText(self._baseText[self.__currId].format(value))

    def getOptions(self) -> Iterable:
        if self.__group.checkedId() == 0:
            # By number
            return None, self.__slider.value() if self.__mode == 'row' else self.__numBox.value()
        else:
            # By perc
            return self.__slider.value() / 100, None

    def setOptions(self, percentage: float, number: int) -> None:
        if percentage is not None:
            self.__group.button(1).click()
            self.__slider.setValue(percentage * 100)
        elif number is not None:
            self.__group.button(0).click()
            self.__slider.setValue(number) if self.__mode == 'row' else self.__numBox.setValue(number)
        else:
            # Both None
            self.__slider.setValue(0)
            self.__numBox.setValue(0)
