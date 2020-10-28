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

from typing import Optional, Union, Dict

from dataMole import data, flogging
from dataMole.gui.editor.interface import AbsOperationEditor
from .interface.graph import InputGraphOperation
from ..gui.editor import OptionsEditorFactory


class SetInput(InputGraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._frame_name: Optional[str] = None

    def execute(self) -> data.Frame:
        """ Get selected dataframe from workbench """
        return self._workbench.getDataframeModelByName(self._frame_name).frame

    @staticmethod
    def name() -> str:
        return 'Copy operation'

    @staticmethod
    def shortDescription() -> str:
        return 'Copy existing dataframe. Should be used as first operation in a pipeline'

    def hasOptions(self) -> bool:
        return bool(self._frame_name)

    def setOptions(self, inputF: str) -> None:
        self._frame_name = inputF

    def getOptions(self) -> Dict[str, Optional[str]]:
        return {'inputF': self._frame_name}

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions():
            return None
        else:
            return self._workbench.getDataframeModelByName(self._frame_name).frame.shape

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withComboBox(key='inputF', label='Input frame', editable=False, model=self._workbench)
        return factory.getEditor()


export = SetInput
