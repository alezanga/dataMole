# -*- coding: utf-8 -*-
#
# Author:       Alessandro Zangari (alessandro.zangari.code@outlook.com)
# Copyright:    © Copyright 2020 Alessandro Zangari, Università degli Studi di Padova
# License:      GPL-3.0-or-later
# Date:         2020-10-04
# Version:      1.0
#
# This file is part of DataMole.
#
# DataMole is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# DataMole is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DataMole.  If not, see <https://www.gnu.org/licenses/>.

import re
from abc import abstractmethod, ABCMeta, ABC
from typing import Any, List, Optional, Dict, Union, Tuple, Set

from PySide2.QtCore import Slot, Signal
from PySide2.QtGui import QIcon, QPixmap, Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QComboBox, QCompleter, QLabel, \
    QSizePolicy, QButtonGroup, QGridLayout, QRadioButton, QCheckBox, QMessageBox, QStyle, QHBoxLayout, \
    QApplication, QFileDialog

from dataMole import data
from dataMole.data.types import Type
from dataMole.operation.utils import SingleStringValidator


class QtABCMeta(type(QWidget), ABCMeta):
    pass


def getStandardIcon(icon: Union[QMessageBox.Icon, QStyle.StandardPixmap], size: int) -> QPixmap:
    style: QStyle = QApplication.style()
    tmpIcon: QIcon
    if icon == QMessageBox.Information or icon == QStyle.SP_MessageBoxInformation:
        tmpIcon = style.standardIcon(QStyle.SP_MessageBoxInformation, None, None)
    elif icon == QMessageBox.Warning or icon == QStyle.SP_MessageBoxWarning:
        tmpIcon = style.standardIcon(QStyle.SP_MessageBoxWarning, None, None)
    elif icon == QMessageBox.Critical or icon == QStyle.SP_MessageBoxCritical:
        tmpIcon = style.standardIcon(QStyle.SP_MessageBoxCritical, None, None)
    elif icon == QMessageBox.Question:
        tmpIcon = style.standardIcon(QStyle.SP_MessageBoxQuestion, None, None)
    else:
        tmpIcon = style.standardIcon(icon, None, None)
    if not tmpIcon.isNull():
        return tmpIcon.pixmap(size, size)
    return QPixmap()


class OptionWidget(QWidget, ABC, metaclass=QtABCMeta):
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

        :return: the value currently set
        """
        pass

    @abstractmethod
    def setData(self, data: Any) -> None:
        """ Set value to be displayed in the custom widget. Receives the value as stored in Options,
        so any conversion must be done here if necessary.
        """
        pass

    def setError(self, msg: str = '', qlabel: QLabel = None) -> None:
        """ Show a validation error below the widget """
        if self._layout.indexOf(self._error) == -1:
            # If error is not present
            if qlabel is not None:
                self._error.deleteLater()
                self._error = qlabel
            else:
                self._error.setStyleSheet('color: red;')
                self._error.setText(msg)
            self._layout.addWidget(self._error)
            self._error.show()

    def unsetError(self) -> None:
        """ Hide the error message if it was set """
        if self._layout.indexOf(self._error) != -1:
            # If error is present
            self._layout.removeWidget(self._error)
            self._error.clear()
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

    def setError(self, msg: str = '', qlabel: QLabel = None, style: str = None) -> None:
        self._textbox.setStyleSheet('border: 1px solid red' if not style else style)
        super().setError(msg, qlabel)

    def unsetError(self) -> None:
        self._textbox.setStyleSheet('')
        super().unsetError()


class AttributeComboBox(OptionWidget):
    """ A combo box for selection of a column, with optional type filter """

    def __init__(self, shape: data.Shape, typesFilter: List[Type], label: str = '',
                 parent: QWidget = None):
        super().__init__(label, parent)
        self._inputShape: data.Shape = None
        self._typesFilter: List[Type] = None
        self._attribute = QComboBox()
        self._attribute.setEditable(True)
        self.refresh(shape, typesFilter)
        self._layout.addWidget(self._attribute)

    def refresh(self, shape: data.Shape, typesFilter: List[Type]) -> None:
        self._inputShape: data.Shape = shape
        self._typesFilter: List[Type] = typesFilter
        if shape:
            self._attributelist = ['{} ({})'.format(n, str(t.name)) for n, t in zip(shape.colNames,
                                                                                    shape.colTypes) if
                                   t in typesFilter]
        else:
            self._attributelist = list()
        completer = QCompleter(self._attributelist, self)
        self._attribute.setModel(completer.model())
        self._attribute.setCompleter(completer)

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
        self.glayout.setVerticalSpacing(10)
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


class MessageLabel(QWidget):
    # WordWrap should be fixed
    def __init__(self, text: str, icon: Union[QMessageBox.Icon, QStyle.StandardPixmap, None] = None,
                 color: Optional[str] = None, parent: QWidget = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        if icon:
            size = 20
            iconLabel = QLabel(self)
            iconLabel.setContentsMargins(0, 0, 0, 0)
            iconLabel.setMargin(0)
            iconLabel.setPixmap(getStandardIcon(icon, size))
            iconLabel.setFixedSize(size, size)
            layout.addWidget(iconLabel, 1, Qt.AlignLeft | Qt.AlignVCenter)
            iconLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            layout.addSpacing(6)
        self._textLabel = QLabel(self)
        self._textLabel.setContentsMargins(0, 0, 0, 0)
        self._textLabel.setText(text)
        if color:
            self._textLabel.setStyleSheet('color: {}'.format(color))
        self._textLabel.setMargin(0)
        layout.addWidget(self._textLabel, 60, Qt.AlignLeft)
        self._textLabel.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        # self._textLabel.setWordWrap(True)

    def setText(self, text: str) -> None:
        self._textLabel.setText(text)

    def setTextColor(self, color: str) -> None:
        self._textLabel.setStyleSheet('color: {}'.format(color))

    def text(self) -> str:
        return self._textLabel.text()


class ReplaceAttributesWidget(QWidget):
    """ A widget that allow the user to specify an attribute suffix and warn him if there are
    duplicate names """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__replaceCB = QCheckBox('Create new column?', self)
        self.__suffixLE = QLineEdit(self)
        self.__suffixLE.setValidator(SingleStringValidator())
        self.__suffixLE.setPlaceholderText('New column name')
        self.__warnLabel = MessageLabel('', QMessageBox.Warning, 'orange', self)
        self.__layout = QHBoxLayout(self)
        self.__warnLayout = QVBoxLayout()
        self.__layout.addWidget(self.__replaceCB)
        self.__layout.addLayout(self.__warnLayout)

        self.__warnLayout.addWidget(self.__suffixLE)
        self.__warnLayout.addWidget(self.__warnLabel)
        self.__warnLabel.hide()
        self.__selectedNames: Set[str] = set()
        self.__columnNames: Set[str] = set()
        self.__suffixLE.setDisabled(True)  # By default checkbox is unchecked and field is disabled
        self.__replaceCB.toggled.connect(self.onCBToggle)

    # @Slot(int)
    # def addColumn(self, pos: int) -> None:
    #     """ Slot to call when a new attribute is selected """
    #     name = self.__shape.colNames[pos]
    #     newName = name + self.__suffixLE.text().strip()
    #     self.__columnNames.add(newName)
    #
    # @Slot(int)
    # def removeColumn(self, pos: int) -> None:
    #     """ Slot to call when a new attribute is removed """
    #     name = self.__shape.colNames[pos]
    #     newName = name + self.__suffixLE.text().strip()
    #     self.__columnNames.discard(newName)

    @Slot(bool)
    def onCBToggle(self, checked: bool) -> None:
        if checked:
            self.__suffixLE.setEnabled(True)
        else:
            self.__suffixLE.setDisabled(True)

    def setData(self, val: Tuple[bool, Optional[str]]) -> None:
        self.__replaceCB.setChecked(val[0])
        if val[0]:
            self.__suffixLE.setText(val[1])

    def getData(self) -> Tuple[bool, Optional[str]]:
        return self.__replaceCB.isChecked(), self.__suffixLE.text()

    # @Slot(str)
    # def _suffixChanged(self, suffix: str) -> None:
    #     self.__selectedNames = {n + suffix for n in self.__selectedNames}
    #     duplicates = self.__selectedNames & self.__columnNames
    #     if duplicates:
    #         labels = ', '.join(["{:s}".format(n) for n in duplicates])
    #         self.__warnLabel.setText('Duplicate names will be replaced: {:s}'.format(labels))
    #         self.__warnLabel.show()
    #     elif self.__warnLabel.isVisible():
    #         self.__warnLabel.hide()


class FileIODialog(QWidget):
    """ A file dialog wrapper over Qt functions """
    fileSelected = Signal(str)

    def __init__(self, parent: QWidget, mode: str, caption: str, filter: str, **kwargs):
        super().__init__(parent)
        self._caption = caption
        self._filter = filter
        self._mode = mode  # {save, load}
        self._kwargs = kwargs

    @Slot()
    def showDialog(self) -> None:
        if self._mode == 'save':
            self._showSaveDialog()
        elif self._mode == 'load':
            self._showLoadDialog()

    def _showSaveDialog(self) -> None:
        path, ext = QFileDialog.getSaveFileName(self.parentWidget(), caption=self._caption,
                                                filter=self._filter, **self._kwargs)
        # Add extension to filename
        path = getFileNameWithExtension(path, ext)
        self.fileSelected.emit(path)

    def _showLoadDialog(self) -> None:
        path, ext = QFileDialog.getOpenFileName(self.parentWidget(), caption=self._caption,
                                                filter=self._filter, **self._kwargs)
        self.fileSelected.emit(path)


def getFileNameWithExtension(path: str, ext: str) -> str:
    """
    Computes the complete name with extension in the following way:
        - if the file name already has an extension it uses that name
        - otherwise it appends the extension to the file name
    """
    # Add extension to filename
    splitPath = path.split('.')
    if len(splitPath) == 1:
        # No extension was added, so use selected extension
        sel = re.search('\\(.*\\)', ext)
        if sel:
            ext = sel.group(0).split('.')[-1][:-1]
            path += '.' + ext
    # else: Extension is present, use that
    return path
