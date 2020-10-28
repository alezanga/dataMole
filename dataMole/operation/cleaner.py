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

from typing import Iterable, Dict, Any, List, Optional

import pandas as pd
import prettytable as pt

from dataMole import data, flogging
from dataMole import exceptions as exp
from dataMole.gui.editor import AbsOperationEditor, OptionsEditorFactory
from dataMole.gui.mainmodels import FrameModel
from dataMole.operation.interface.graph import GraphOperation
from .utils import numpy_equal


def find_duplicates(df: pd.DataFrame) -> List[str]:
    # Convert categories to str
    catTypes: List[str] = df.select_dtypes(include='category').columns.to_list()
    notCat: List[str] = df.select_dtypes(exclude='category').columns.to_list()

    if catTypes:
        copy_df = df[catTypes].astype(object)
        copy_df = pd.concat([copy_df, df[notCat]], axis=1)
    else:
        copy_df = df

    groups = copy_df.columns.to_series().groupby(copy_df.dtypes).groups
    duplicates = list()

    for t, v in groups.items():
        cs = copy_df[v].columns
        vs = copy_df[v]
        lcs = len(cs)
        for i in range(lcs):
            ia = vs.iloc[:, i].values
            for j in range(i + 1, lcs):
                ja = vs.iloc[:, j].values
                if numpy_equal(ia, ja):
                    duplicates.append(cs[j])
                    break
    return duplicates


class RemoveBijections(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__selected: List[int] = list()

    def logOptions(self) -> str:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Selected columns'])
        for a in self.__selected:
            tt.add_row([columns[a]])
        return tt.get_string(vrules=pt.ALL, border=True)

    def execute(self, df: data.Frame) -> data.Frame:
        df = df.getRawFrame()
        colOrder: List[str] = df.columns.to_list()

        subDf = df.iloc[:, self.__selected]

        duplicates = find_duplicates(subDf)

        if duplicates:
            df = df.copy(True)
            df = df.drop(duplicates, axis=1)
            # Keep original order
            order = [c for c in colOrder if c not in duplicates]
            df = df[order]
        return data.Frame(df)

    @staticmethod
    def name() -> str:
        return 'RemoveBijections'

    @staticmethod
    def shortDescription() -> str:
        return 'Removes columns with the same values but with different names. Only selected columns ' \
               'will be considered for removal. Match is always performed over all columns'

    def hasOptions(self) -> bool:
        return bool(self.__selected)

    def unsetOptions(self) -> None:
        self.__selected = list()

    def needsOptions(self) -> bool:
        return True

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return False

    @staticmethod
    def needsInputShapeKnown() -> bool:
        return True

    def getOutputShape(self) -> Optional[data.Shape]:
        return None

    def getOptions(self) -> Iterable:
        options = {k: None for k in self.__selected}
        return {'attributes': options}

    def setOptions(self, attributes: Dict[int, Dict[str, Any]]) -> None:
        selection = list(attributes.keys())
        if not selection:
            raise exp.OptionValidationError([('noOptions', 'Error: no attributes are selected')])
        self.__selected = selection

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, False, None, None)
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.setSizeHint(400, 600)
        editor.attributes.setSourceFrameModel(FrameModel(editor, self.shapes[0]))

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


export = RemoveBijections
