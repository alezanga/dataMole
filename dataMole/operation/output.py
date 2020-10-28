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

from typing import Optional, Iterable

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget

from dataMole import data, flogging
from dataMole.gui.editor.interface import AbsOperationEditor
from .interface.graph import OutputGraphOperation
from ..gui import utils as opw


class ToVariableOp(OutputGraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__var_name: Optional[str] = None

    def execute(self, df: data.Frame) -> None:
        self._workbench.setDataframeByName(self.__var_name, df)

    @staticmethod
    def name() -> str:
        return 'To variable'

    @staticmethod
    def shortDescription() -> str:
        return 'Save the output as a variable in the workbench with the given name'

    def hasOptions(self) -> bool:
        return bool(self.__var_name)

    def setOptions(self, var_name: Optional[str]) -> None:
        self.__var_name = var_name

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return [self.__var_name]

    def getEditor(self) -> AbsOperationEditor:
        class WriteEditor(AbsOperationEditor):
            def editorBody(self) -> QWidget:
                self.__outputBox = opw.TextOptionWidget()
                return self.__outputBox

            def getOptions(self) -> Iterable:
                text = self.__outputBox.getData()
                return [text]

            def setOptions(self, var_name: str) -> None:
                self.__outputBox.widget.textChanged.connect(self.testInput)
                if var_name:
                    self.__outputBox.setData(var_name)

            @Slot(str)
            def testInput(self, name: str):
                if name not in self.workbench.names:
                    self.__outputBox.unsetError()
                else:
                    self.__outputBox.setError('Variable "{:s}" will be replaced'.format(name),
                                              style='border: 1px solid orange')

        return WriteEditor()


export = ToVariableOp
