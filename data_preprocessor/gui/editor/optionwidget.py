from abc import abstractmethod, ABCMeta
from typing import Any, List, Optional

from PySide2.QtCore import QObject
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QComboBox, QCompleter, QLabel, QSizePolicy

from data_preprocessor import data
from data_preprocessor.data.types import Types


class QtABCMeta(type(QObject), ABCMeta):
    pass


class OptionWidget(QWidget, metaclass=QtABCMeta):
    """ Represents the interface of an editor for a single option """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._error = QLabel(self)
        self._layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self._error.setSizePolicy(QSizePolicy.MinimumExpanding)

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
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
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
    def __init__(self, shape: data.Shape, typesFilter: List[Types], parent: QWidget = None):
        super().__init__(parent)

        self._inputShape: data.Shape = shape
        self._typesFilter: List[Types] = typesFilter
        if shape:
            self._attributelist = [n for n, t in zip(shape.col_names, shape.col_types) if
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