from abc import abstractmethod, ABCMeta
from typing import Any, List, Optional, Dict

from PySide2.QtCore import QObject
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QComboBox, QCompleter, QLabel, \
    QSizePolicy, QButtonGroup, QGridLayout, QRadioButton

from data_preprocessor import data
from data_preprocessor.data.types import Types


class QtABCMeta(type(QObject), ABCMeta):
    pass


class OptionWidget(QWidget, metaclass=QtABCMeta):
    """ Represents the interface of an editor for a single option """

    def __init__(self, label: str = '', parent: QWidget = None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._error = QLabel(self)
        self._layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self._error.setWordWrap(True)
        self._error.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        if label:
            self._layout.addWidget(QLabel(label))
        self.setContentsMargins(0, 0, 0, 0)

    @property
    @abstractmethod
    def widget(self) -> QWidget:
        """ Return the internal widget """
        pass

    @abstractmethod
    def getData(self) -> Any:
        """ Get current option value. Should provide it in the exact value that Options expect.
        If the value is not set return None.

        :return the value currently set
        """
        pass

    @abstractmethod
    def setData(self, data: Any) -> None:
        """ Set value to be displayed in the custom widget. Receives the value as stored in Options,
        so any conversion must be done here if necessary.
        """
        pass

    def setError(self, msg: str) -> None:
        """ Show a validation error below the widget """
        if self._layout.indexOf(self._error) == -1:
            # If error is not present
            self._error.setStyleSheet('color: red;')
            self._error.setText(msg)
            self._layout.addWidget(self._error)
            self._error.show()

    def unsetError(self) -> None:
        """ Hide the error message if it was set """
        if self._layout.indexOf(self._error) != -1:
            # If error is present
            self._layout.removeWidget(self._error)
            self._error.hide()


class TextOptionWidget(OptionWidget):
    def __init__(self, label: str = '', parent: QWidget = None):
        super().__init__(label, parent)
        self._textbox = QLineEdit()
        self._layout.addWidget(self._textbox)

    @property
    def widget(self) -> QWidget:
        return self._textbox

    def getData(self) -> str:
        text = self._textbox.text()
        return text if text else None

    def setData(self, val: str) -> None:
        if val:
            self._textbox.setText(val)

    def setError(self, msg: str) -> None:
        self._textbox.setStyleSheet('border: 1px solid red')
        super().setError(msg)

    def unsetError(self) -> None:
        self._textbox.setStyleSheet('')
        super().unsetError()


class AttributeComboBox(OptionWidget):
    def __init__(self, shape: data.Shape, typesFilter: List[Types], label: str = '',
                 parent: QWidget = None):
        super().__init__(label, parent)

        self._inputShape: data.Shape = shape
        self._typesFilter: List[Types] = typesFilter
        if shape:
            self._attributelist = ['{} ({})'.format(n, str(t.value)) for n, t in zip(shape.col_names,
                                                                                     shape.col_types) if
                                   t in typesFilter]
        else:
            self._attributelist = list()

        self._attribute = QComboBox()
        self._attribute.setEditable(True)
        completer = QCompleter(self._attributelist, self)
        self._attribute.setModel(completer.model())
        self._attribute.setCompleter(completer)
        self._layout.addWidget(self._attribute)

    @property
    def widget(self) -> QWidget:
        return self._attribute

    def getData(self) -> Optional[int]:
        return self._attribute.currentIndex() if self._attribute.currentText() else None

    def setData(self, selected: Optional[int]) -> None:
        if selected is not None:
            self._attribute.setCurrentIndex(selected)
        else:
            self._attribute.setCurrentIndex(0)


class RadioButtonGroup(OptionWidget):
    _MAX_BUTTONS_ROW = 4

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        wlabel = QLabel(label, self)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.glayout = QGridLayout(self)
        self.glayout.setVerticalSpacing(20)
        self.glayout.addWidget(wlabel, 0, 0, 1, -1)
        self.__row = 1
        self.__col = 0
        # dict {buttonId: value}
        self.valueDict: Dict[int, Any] = dict()

    @property
    def widget(self) -> QWidget:
        return self.group

    def addRadioButton(self, label: str, value: Any, checked: bool) -> None:
        but = QRadioButton(text=label, parent=self)
        self.group.addButton(but)
        self.valueDict[self.group.id(but)] = value
        if checked or len(self.group.buttons()) == 1:
            but.setChecked(True)
        self.glayout.addWidget(but, self.__row, self.__col, 1, 1)
        self.__col += 1
        if self.__col % self._MAX_BUTTONS_ROW == 0:
            self.__row += 1
            self.__col = 0

    def getData(self) -> Any:
        """ Return value associated to selected button """
        cid = self.group.checkedId()
        return self.valueDict[cid] if cid != -1 else None

    def setData(self, data: Any) -> None:
        for bid, d in self.valueDict.items():
            if d == data:
                self.group.button(bid).setChecked(True)
                break
