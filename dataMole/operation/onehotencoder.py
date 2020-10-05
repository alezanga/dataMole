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

from operator import itemgetter
from typing import List, Union, Dict

import pandas as pd
import prettytable as pt

from dataMole import data, flogging
from dataMole.data.types import Types, Type
from dataMole.gui.editor import AbsOperationEditor, OptionsEditorFactory
from dataMole.gui.mainmodels import FrameModel
from dataMole.operation.interface.graph import GraphOperation


class OneHotEncoder(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attributes: List[int] = list()
        self.__includeNan: bool = False

    def logOptions(self) -> None:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Selected columns'])
        for a in self.__attributes:
            tt.add_row([columns[a]])
        tt.align = 'l'
        return tt.get_string(border=True, vrules=pt.ALL) + '\nWith Nan column: {:b}'.format(
            self.__includeNan)

    def execute(self, df: data.Frame) -> data.Frame:
        pdf = df.getRawFrame().copy(deep=True)
        prefixes = itemgetter(*self.__attributes)(self.shapes[0].colNames)
        npdf = pd.get_dummies(pdf.iloc[:, self.__attributes], prefix=prefixes,
                              dummy_na=self.__includeNan, dtype=int)
        npdf = npdf.astype('category', copy=False)
        # Replace eventual duplicate columns
        pdf = pdf.drop(columns=npdf.columns, errors='ignore')
        # Avoid dropping original columns (just append)
        # pdf = pdf.drop(columns[self.__attributes], axis=1, inplace=False)
        pdf = pd.concat([pdf, npdf], axis=1)
        return data.Frame(pdf)

    @staticmethod
    def name() -> str:
        return 'One-hot encoder'

    @staticmethod
    def shortDescription() -> str:
        return 'Replace every categorical value with a binary attribute'

    def hasOptions(self) -> bool:
        if self.__attributes and self.__includeNan is not None:
            return True
        return False

    def unsetOptions(self) -> None:
        self.__attributes = list()

    def needsOptions(self) -> bool:
        return True

    def acceptedTypes(self) -> List[Type]:
        return [Types.Ordinal, Types.Nominal, Types.String]

    def getOptions(self) -> Dict[str, Union[Dict[int, None], bool]]:
        return {
            'attributes': {k: None for k in self.__attributes},
            'includeNan': self.__includeNan
        }

    def setOptions(self, attributes: Dict[int, None], includeNan: bool) -> None:
        self.__attributes = list(attributes.keys())
        self.__includeNan = includeNan

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True, None, self.acceptedTypes())
        factory.withCheckBox('Column for nan', 'includeNan')
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.attributes.setSourceFrameModel(FrameModel(editor, self._shapes[0]))

    def getOutputShape(self) -> Union[data.Shape, None]:
        return None

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


export = OneHotEncoder
