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

import copy
from enum import Enum
from typing import Iterable, List, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
import prettytable as pt
import sklearn.preprocessing as skp
from PySide2.QtCore import QModelIndex, QAbstractItemModel
from PySide2.QtGui import QIntValidator, Qt
from PySide2.QtWidgets import QHeaderView, QStyledItemDelegate, QLineEdit, QWidget

from dataMole import data, exceptions as exp, flogging
from dataMole.data.types import Types, Type
from dataMole.gui.editor import OptionsEditorFactory, OptionValidatorDelegate, \
    AbsOperationEditor
from dataMole.gui.mainmodels import FrameModel
from dataMole.operation.interface.graph import GraphOperation
from dataMole.operation.utils import NumericListValidator, MixedListValidator, splitString, \
    joinList, isFloat


class BinStrategy(Enum):
    Uniform = 'uniform'
    Quantile = 'quantile'
    Kmeans = 'kmeans'


class BinsDiscretizer(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__strategy: BinStrategy = BinStrategy.Uniform
        self.__attributes: Dict[int, int] = dict()
        self.__attributeSuffix: Optional[str] = '_discretized'

    def __logExecution(self, columns: List[str], binEdges: Dict[int, List[float]]) -> None:
        optPt = pt.PrettyTable(field_names=['Option', 'Value'])
        optPt.add_row(['Strategy', self.__strategy.value])
        optPt.add_row(['Drop transformed',
                       'False' if not self.__attributeSuffix else 'True ({})'.format(
                           self.__attributeSuffix)])

        binsPt = pt.PrettyTable(field_names=['Column', 'K', 'Computed bins', 'Actual K'])
        for i, k in self.__attributes.items():
            iEdges = binEdges[i]
            binsPt.add_row([columns[i], k, ', '.join(['{:G}'.format(e) for e in iEdges]), len(iEdges)])

        self._logOptionsString = optPt.get_string(border=True, vrules=pt.ALL)
        self._logExecutionString = binsPt.get_string(border=True, vrules=pt.ALL)

    def execute(self, df: data.Frame) -> data.Frame:
        frame = copy.deepcopy(df)
        f = frame.getRawFrame()
        # Operation ignores nan values
        nanRows = f.iloc[:, list(self.__attributes.keys())].isnull()
        # For every column, transform every non-nan row
        columns = f.columns
        edges: Dict[int, List[float]] = dict()
        for col, k in self.__attributes.items():
            colName = columns[col]
            notNa = (~nanRows.loc[:, colName]).to_list()
            discretizer = skp.KBinsDiscretizer(n_bins=k, encode='ordinal',
                                               strategy=self.__strategy.value)
            # Discretize and convert to string (since categories are strings)
            result = discretizer.fit_transform(f.loc[notNa, colName].values.reshape(-1, 1)).astype(str)
            name: str = colName
            if self.__attributeSuffix:
                # Make a new column with all nans
                name = colName + self.__attributeSuffix
                f.loc[:, name] = np.nan
            # Assign column
            f.loc[notNa, [name]] = result
            f.loc[:, name] = f[name].astype(
                pd.CategoricalDtype(categories=[str(float(i)) for i in range(k)], ordered=True))
            edges[col] = discretizer.bin_edges_[0].tolist()
        # Log what has been done
        self.__logExecution(columns, edges)
        return data.Frame(f)

    def acceptedTypes(self) -> List[Type]:
        return [Types.Numeric]

    @staticmethod
    def name() -> str:
        return 'KBinsDiscretizer'

    @staticmethod
    def shortDescription() -> str:
        return 'Discretize numeric values into equal sized bins'

    def hasOptions(self) -> bool:
        return self.__attributes and self.__strategy is not None

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        options: Dict[
            str, Union[Dict[int, Dict[str, str]], BinStrategy, Tuple[bool, Optional[str]]]] = dict()
        options['attributes'] = dict()
        for r, bins in self.__attributes.items():
            options['attributes'][r] = {'bins': str(bins)}
        options['strategy'] = self.__strategy
        options['suffix'] = (bool(self.__attributeSuffix), self.__attributeSuffix)
        return options

    def setOptions(self, attributes: Dict[int, Dict[str, str]], strategy: BinStrategy,
                   suffix: Tuple[bool, Optional[str]]) -> None:
        # Validate options
        def isPositiveInteger(x):
            try:
                y = int(x)
            except ValueError:
                return False
            else:
                if y > 1:
                    return True
                return False

        errors = list()
        if not attributes:
            errors.append(('nosel', 'Error: At least one attribute should be selected'))
        for r, options in attributes.items():
            bins = options.get('bins', None)
            if not bins:
                errors.append(('nooption', 'Error: Number of bins must be set at row {:d}'.format(r)))
            elif not isPositiveInteger(bins):
                errors.append(('binsNotInt', 'Error: Number of bins must be > 1 at row {:d}'.format(r)))
        if strategy is None:
            errors.append(('missingStrategy', 'Error: Strategy must be set'))
        if suffix[0] and not suffix[1]:
            errors.append(('suffix', 'Error: suffix for new attribute must be specified'))
        if errors:
            raise exp.OptionValidationError(errors)
        # Clear attributes
        self.__attributes = dict()
        # Set options
        for r, options in attributes.items():
            k = int(options['bins'])
            self.__attributes[r] = k
        self.__strategy = strategy
        self.__attributeSuffix = suffix[1] if suffix[0] else None

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True,
                                   {
                                       'bins': (
                                           'K', OptionValidatorDelegate(QIntValidator(1, 10000000)), None
                                       )}, types=self.acceptedTypes())
        values = [(s.name, s) for s in BinStrategy]
        factory.withRadioGroup('Select strategy:', 'strategy', values)
        factory.withAttributeNameOptionsForTable('suffix')
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.setSizeHint(500, 600)
        # Set frame model
        editor.attributes.setSourceFrameModel(FrameModel(editor, self.shapes[0]))
        # Stretch new section
        editor.attributes.tableView.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions() or self.shapes[0] is None:
            return None
        s = self.shapes[0].clone()
        if not self.__attributeSuffix:
            # Shape does not change
            for col in self.__attributes.keys():
                s.colTypes[col] = Types.Ordinal
        else:
            d = s.columnsDict
            for col in self.__attributes.keys():
                colName: str = self.shapes[0].colNames[col] + self.__attributeSuffix
                d[colName] = Types.Ordinal
            s = data.Shape.fromDict(d, s.indexDict)
        return s

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


class RangeDiscretizer(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # { col: (edges, labels) }
        self.__attributes: Dict[int, Tuple[List[float], List[str]]] = dict()
        self.__attributeSuffix: Optional[str] = '_bins'

    def logOptions(self) -> None:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Column', 'Ranges', 'Labels'])
        for i, opts in self.__attributes.items():
            tt.add_row([columns[i],
                        ', '.join(
                            ['({:G}, {:G}]'.format(a, b) for a, b in zip(opts[0], opts[0][1:])]),
                        ', '.join(opts[1])])
        drop: str = '\nNew attribute suffix: {}'.format(self.__attributeSuffix)

        return tt.get_string(border=True, vrules=pt.ALL) + drop

    def execute(self, df: data.Frame) -> data.Frame:
        f = df.getRawFrame().copy(True)
        columns = f.columns.to_list()
        for c, o in self.__attributes.items():
            result = pd.cut(f.iloc[:, c], bins=o[0], labels=o[1], duplicates='drop')
            colName: str = columns[c]
            newColName: str = colName if not self.__attributeSuffix else colName + self.__attributeSuffix
            f.loc[:, newColName] = result
        return data.Frame(f)

    def getOutputShape(self) -> Optional[data.Shape]:
        if self.shapes[0] is None or not self.hasOptions():
            return None
        s = self.shapes[0].clone()
        if not self.__attributeSuffix:
            for c in self.__attributes.keys():
                s.colTypes[c] = Types.Ordinal
        else:
            d = s.columnsDict
            for c in self.__attributes.keys():
                colName: str = s.colNames[c] + self.__attributeSuffix
                d[colName] = Types.Ordinal  # Overwrites existing columns
            s = data.Shape.fromDict(d, s.indexDict)
        return s

    @staticmethod
    def name() -> str:
        return 'RangeDiscretizer'

    @staticmethod
    def shortDescription() -> str:
        return 'Discretize numeric attributes in user defined ranges'

    def acceptedTypes(self) -> List[Type]:
        return [Types.Numeric]

    def hasOptions(self) -> bool:
        return bool(self.__attributes)

    def unsetOptions(self) -> None:
        self.__attributes: Dict[int, Tuple[List[float], List[str]]] = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        options = dict()
        options['table'] = dict()
        for row, opt in self.__attributes.items():
            options['table'][row] = {'bins': opt[0],  # List[float]
                                     'labels': joinList(opt[1], sep=' ')  # str
                                     }
        options['suffix'] = (bool(self.__attributeSuffix), self.__attributeSuffix)
        return options

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        options = {
            'bins': ('Bin edges', _RangeDelegate(), None),
            'labels': ('Labels', OptionValidatorDelegate(MixedListValidator()), None)
        }
        factory.withAttributeTable('table', True, False, True, options, self.acceptedTypes())
        factory.withAttributeNameOptionsForTable('suffix')
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.setSizeHint(500, 600)
        # Set frame model
        editor.table.setSourceFrameModel(FrameModel(editor, self.shapes[0]))
        # Stretch new section
        editor.table.tableView.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        editor.table.tableView.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

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

    def setOptions(self, table: Dict[int, Dict[str, Union[List[float], str]]],
                   suffix: Tuple[bool, Optional[str]]) -> None:
        # Validate options
        errors = list()
        if not table:
            errors.append(('noAttr', 'Error: at least one attribute should be chosen'))
        if suffix[0] and not suffix[1]:
            errors.append(('suffix', 'Error: new attribute suffix must be specified'))
        if errors:
            raise exp.OptionValidationError(errors)
        options: Dict[int, Tuple[List[float], List[str]]] = dict()
        for row, opts in table.items():
            if not opts.get('bins', None) or not opts.get('labels', None):
                errors.append(('notSet', 'Error: options at row {:d} are not set'.format(row)))
                continue
            # Edges are already parsed by delegate
            edges: List[float] = opts['bins']
            # Labels must be parsed
            labels: List[str] = splitString(opts['labels'], sep=' ')
            labNum = len(edges) - 1
            if len(labels) != labNum:
                errors.append(('invalidLabels',
                               'Error: Labels at row {:d} is not equal to the number of intervals '
                               'defined ({:d})'.format(row, labNum)))
            options[row] = (edges, labels)
            if len(errors) > 8:
                break
        if errors:
            raise exp.OptionValidationError(errors)
        # If everything went well set options
        self.__attributes = options
        self.__attributeSuffix = suffix[1] if suffix[0] else None


class _RangeDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget:
        le = QLineEdit(parent)
        le.setValidator(NumericListValidator(float_int=float, parent=parent))
        return le

    def displayText(self, value: List[float], locale) -> str:
        return ' '.join(['({:G}, {:G}]'.format(p, q) for p, q in zip(value, value[1:])])

    def setEditorData(self, editor: QLineEdit, index: QModelIndex) -> None:
        ranges: Optional[List[float]] = index.data(Qt.EditRole)
        if ranges:
            editor.setText(' '.join(['{:G}'.format(r) for r in ranges]))

    def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex) -> None:
        stringList: str = editor.text()
        stringEdges: List[str] = splitString(stringList, sep=' ')
        # If number are valid set them, otherwise leave them unchanged
        if all(map(isFloat, stringEdges)):
            edges: List[float] = [float(x) for x in stringEdges]
            model.setData(index, edges, Qt.EditRole)


export = [BinsDiscretizer, RangeDiscretizer]
