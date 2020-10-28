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

import os
from typing import Dict

import pandas as pd
from PySide2.QtCore import Slot

from dataMole import data, exceptions as exp
from dataMole.gui.editor import OptionsEditorFactory, AbsOperationEditor
from dataMole.operation.interface.operation import Operation


class PickleLoader(Operation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__file: str = None
        self.__frameName: str = None

    def execute(self) -> None:
        df = pd.read_pickle(self.__file)
        self._workbench.setDataframeByName(self.__frameName, data.Frame(df))

    @staticmethod
    def shortDescription() -> str:
        return 'Load a dataframe from pickle file'

    def setOptions(self, file: str, frameName: str) -> None:
        errors = list()
        frameName = frameName.strip()
        if not file:
            errors.append(('file', 'Error: no file name is specified'))
        if not frameName:
            errors.append(('nameError', 'Error: a valid frame name must be specified'))
        if errors:
            raise exp.OptionValidationError(errors)

        self.__file = file
        self.__frameName = frameName

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> 'AbsOperationEditor':
        factory = OptionsEditorFactory()
        factory.initEditor(subclass=CustomPickleLoadEditor)
        factory.withFileChooser(key='file', label='Select a file', extensions='Pickle (*.pickle)',
                                mode='load')
        factory.withTextField(key='frameName', label='Dataframe name')
        return factory.getEditor()

    def injectEditor(self, editor: 'CustomPickleLoadEditor') -> None:
        editor.file.textChanged.connect(editor.setNameFromFile)

    @staticmethod
    def name() -> str:
        return 'Load pickle'

    @staticmethod
    def shortDescription() -> str:
        return 'Load an object in Python serialized format'

    def longDescription(self) -> str:
        return 'Notes: pickle represents an arbitrary Python object, but this operation expects it to ' \
               'be a Pandas dataframe. Any different object will cause an error.'


class CustomPickleLoadEditor(AbsOperationEditor):
    @Slot(str)
    def setNameFromFile(self, path: str) -> None:
        if path and not self.frameName.text():
            name: str = os.path.splitext(os.path.basename(path))[0]
            self.frameName.setText(name)


class PickleWriter(Operation):
    def __init__(self, frameName: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__file: str = None
        self.__frame: str = frameName

    @staticmethod
    def name() -> str:
        return 'Write pickle'

    def execute(self) -> None:
        df: pd.DataFrame = self._workbench.getDataframeModelByName(self.__frame).frame.getRawFrame()
        df.to_pickle(self.__file)

    def setOptions(self, file: str, frame: str) -> None:
        errors = list()
        if not file:
            errors.append(('file', 'Error: no file name is specified'))
        if not frame:
            errors.append(('frame', 'Error: input frame must be valid'))
        if errors:
            raise exp.OptionValidationError(errors)
        self.__file = file
        self.__frame = frame

    @staticmethod
    def shortDescription() -> str:
        return 'Write a dataframe to pickle'

    def getOptions(self) -> Dict:
        return {'frame': self.__frame, 'file': self.__file}

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> 'AbsOperationEditor':
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withComboBox('Frame to write', 'frame', False, model=self.workbench)
        factory.withFileChooser(key='file', label='Write to', extensions='Pickle (*.pickle)',
                                mode='save')
        return factory.getEditor()
