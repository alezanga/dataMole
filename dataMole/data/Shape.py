# -*- coding: utf-8 -*-
#
# Author:       Alessandro Zangari
# Contact:      alessandro.zangari.code@outlook.com
# Copyright:    © Copyright 2020 Alessandro Zangari, Università degli Studi di Padova
# License:      GPL-3.0-or-later
# Date:         2020-09-21
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

from typing import List, Dict

from dataMole.data.types import Type, IndexType


class Shape:
    """
    Representation of the shape of a Frame
    """

    def __init__(self):
        self.colNames: List[str] = list()
        self.colTypes: List[Type] = list()
        self.index: List[str] = list()
        self.indexTypes: List[IndexType] = list()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.columnsDict == other.columnsDict and self.indexDict == other.indexDict
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return str(self.__dict__)

    def serialize(self) -> Dict:
        """ Serialize a shape object in a dictionary """
        s = self.clone().__dict__
        s['colTypes'] = [t.code for t in self.colTypes]
        s['indexTypes'] = [t.code for t in self.indexTypes]
        # s['colNames'] = [n for n in self.colNames]
        # s['index'] = [n for n in self.index]
        return s

    @staticmethod
    def deserialize(state: Dict) -> 'Shape':
        """ Create a new shape from a serialization """
        s = Shape()
        s.__dict__ = state
        s.colTypes = [Type.fromCode(c) for c in state['colTypes']]
        s.indexTypes = [IndexType(Type.fromCode(c)) for c in state['indexTypes']]
        return s

    def clone(self) -> 'Shape':
        s = Shape()
        s.colNames = [n for n in self.colNames]
        s.index = [n for n in self.index]
        s.colTypes = [t for t in self.colTypes]
        s.indexTypes = [t for t in self.indexTypes]
        return s

    @staticmethod
    def fromDict(columns: Dict[str, Type], indexes: Dict[str, Type] = None) -> 'Shape':
        s = Shape()
        s.colNames = list(columns.keys())
        s.colTypes = list(columns.values())
        if indexes:
            s.index = list(indexes.keys())
            s.indexTypes = list(indexes.values())
        return s

    @property
    def columnsDict(self) -> Dict[str, Type]:
        return dict(zip(self.colNames, self.colTypes))

    @property
    def indexDict(self) -> Dict[str, Type]:
        return dict(zip(self.index, self.indexTypes))

    @property
    def nColumns(self) -> int:
        return len(self.colNames)

    @property
    def nIndexLevels(self) -> int:
        return len(self.index)
