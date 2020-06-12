import logging
from operator import itemgetter
from typing import List, Union, Iterable, Dict, Optional

from PySide2.QtWidgets import QWidget, QHeaderView
from pandas.api.types import CategoricalDtype

from data_preprocessor import data
from data_preprocessor.data.types import Types, inv_type_dict
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.exceptions import OptionValidationError
from .interface.graph import GraphOperation
from .utils import MixedListValidator, splitList, joinList
from ..gui.generic.OptionsEditorFactory import OptionsEditorFactory
from ..gui.mainmodels import SearchableAttributeTableWidget, FrameModel


class ToNumericOp(GraphOperation):
    def __init__(self):
        super().__init__()
        self.__attributes: List[int] = list()

    def hasOptions(self) -> bool:
        if self.__attributes:
            return True
        return False

    def execute(self, df: data.Frame) -> data.Frame:
        # If type of attribute is not accepted
        columns = df.shape.col_types
        items = itemgetter(*self.__attributes)(columns)
        if not all(map(lambda x: x in self.acceptedTypes(),
                       items if isinstance(items, tuple) else (items,))):
            logging.debug('Type not supported for operation {}'.format(self.name()))
            return df
        # Deep copy
        raw_df = df.getRawFrame().copy(deep=True)
        raw_df.iloc[:, self.__attributes] = raw_df.iloc[:, self.__attributes] \
            .apply(lambda c: c.astype(dtype=inv_type_dict[Types.Numeric], errors='raise'))
        return data.Frame(raw_df)

    @staticmethod
    def name() -> str:
        return 'toNumeric'

    def shortDescription(self) -> str:
        return 'Convert one attribute to Numeric values. All types except Datetime can be converted'

    def acceptedTypes(self) -> List[Types]:
        return [Types.String, Types.Categorical]

    def setOptions(self, attribute_indexes: List[int]) -> None:
        self.__attributes = attribute_indexes

    def unsetOptions(self) -> None:
        self.__attributes = list()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return [self.__attributes]

    def getEditor(self) -> AbsOperationEditor:
        return _SelectAttribute()

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions() or not self._shapes[0]:
            return None
        # If type is not accepted
        columns = self._shapes[0].col_types
        items = itemgetter(*self.__attributes)(columns)
        if not all(map(lambda x: x in self.acceptedTypes(),
                       items if isinstance(items, tuple) else (items,))):
            return None
        s = self._shapes[0].copy()
        for i in self.__attributes:
            s.col_types[i] = Types.Numeric
        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

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


class ToCategoricalOp(GraphOperation):
    def __init__(self):
        super().__init__()
        self.__attributes: Dict[int, Optional[List[str]]] = dict()

    def hasOptions(self) -> bool:
        if self.__attributes:
            return True
        return False

    def execute(self, df: data.Frame) -> data.Frame:
        # Deep copy
        raw_df = df.getRawFrame().copy(deep=True)
        # To string
        columnIndexes = list(self.__attributes.keys())
        isNan = raw_df.iloc[:, columnIndexes].isnull()
        raw_df.iloc[(~isNan).index, columnIndexes] = raw_df.iloc[(~isNan).index, columnIndexes].astype(
            dtype=str, errors='raise')
        colNames = df.shape.col_names
        # To category
        conversions: Dict[str, CategoricalDtype] = dict([
            (lambda x: (colNames[x[0]], CategoricalDtype(categories=x[1],
                                                         ordered=False)))(x) for x in
            self.__attributes.items()
        ])
        raw_df.iloc[:, columnIndexes] = raw_df.iloc[:, columnIndexes].astype(
            dtype=conversions, errors='raise')
        return data.Frame(raw_df)

    @staticmethod
    def name() -> str:
        return 'toCategory'

    def shortDescription(self) -> str:
        return 'Convert one attribute to categorical type. Every different value will be considered a ' \
               'new category'

    def acceptedTypes(self) -> List[Types]:
        return [Types.String, Types.Numeric, Types.Categorical]

    def setOptions(self, attributes: Dict[int, Dict[str, str]]) -> None:
        if not attributes:
            raise OptionValidationError([('nooptions', 'Error: select at least one attribute')])
        options: Dict[int, Optional[List[str]]] = dict()
        for c, opt in attributes.items():
            # if not opt:
            #     raise OptionValidationError(
            #         [('notset', 'Error: options at row {:d} are not fully set'.format(c))])
            catString: Optional[str] = opt.get('cat', None)
            categories: Optional[List[str]] = None
            if catString:
                categories = splitList(catString, sep=' ')
                if not categories:
                    categories = None
            options[c] = categories
        # Options are correctly set
        self.__attributes = options

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        options: Dict[int, Dict[str, str]] = dict()
        for c, opt in self.__attributes.items():
            options[c] = {'cat': joinList(opt, sep=' ') if opt else ''}
        return {'attributes': options}

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True, {'cat': ('Categories',
                                                                             MixedListValidator())},
                                   types=self.acceptedTypes())
        e = factory.getEditor()
        # Set frame model
        e.attributes.setSourceFrameModel(FrameModel(e, self.shapes[0]))
        # Stretch new section
        e.attributes.tableView.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        return e

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions() or not self._shapes[0]:
            return None
        # If type is not accepted
        columns = self._shapes[0].col_types
        items = itemgetter(*self.__attributes)(columns)
        if not all(map(lambda x: x in self.acceptedTypes(),
                       items if isinstance(items, tuple) else (items,))):
            return None
        s = self._shapes[0].copy()
        for a in self.__attributes:
            s.col_types[a] = Types.Categorical
        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

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


class _SelectAttribute(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        self.__searchableTable = SearchableAttributeTableWidget(checkable=True,
                                                                showTypes=True,
                                                                filterTypes=self.acceptedTypes)
        self.__searchableTable.setSourceFrameModel(FrameModel(self, self.inputShapes[0]))

        return self.__searchableTable

    def getOptions(self) -> List[List[int]]:
        return [self.__searchableTable.model().checkedAttributes]

    def setOptions(self, selected_indexes: List[int]) -> None:
        self.__searchableTable.model().checkedAttributes = selected_indexes


# class TypeOp(GraphOperation):
#     def __init__(self):
#         super().__init__()
#         self.__types: Dict[int, Types] = dict()
#
#     def execute(self, df: data.Frame) -> data.Frame:
#         """ Changes type """
#         # Deep copy
#         raw_df = df.getRawFrame().copy(deep=True)
#         colnames = df.colnames
#         for k, v in self.__types.items():
#             # Change type in-place (since raw_df is a deep copy)
#             raw_df[colnames[k]] = raw_df[colnames[k]].astype(dtype=inv_type_dict[v], copy=True,
#                                                              errors='raise')
#         return data.Frame(raw_df)
#
#     @staticmethod
#     def name() -> str:
#         return 'Change column type'
#
#     def info(self) -> str:
#         return 'Change type of data columns'
#
#     def acceptedTypes(self) -> List[Types]:
#         return ALL_TYPES
#
#     def setOptions(self, new_types: Dict[int, Types]) -> None:
#         self.__types = new_types
#
#     def unsetOptions(self) -> None:
#         self.__types = dict()
#
#     def getOptions(self) -> Any:
#         return copy.deepcopy(self.__types), self._shapes[0].copy()
#
#     def needsOptions(self) -> bool:
#         return True
#
#     def getEditor(self) -> AbsOperationEditor:
#         pass
#
#     def getOutputShape(self) -> Union[data.Shape, None]:
#         if not self.__types:
#             return copy.deepcopy(self._shapes[0])
#         s = copy.deepcopy(self._shapes[0])
#         for k, v in self.__types.items():
#             s.col_types[k] = v
#         return s
#
#     @staticmethod
#     def isOutputShapeKnown() -> bool:
#         return True
#
#     @staticmethod
#     def minInputNumber() -> int:
#         return 1
#
#     @staticmethod
#     def maxInputNumber() -> int:
#         return 1
#
#     @staticmethod
#     def minOutputNumber() -> int:
#         return 1
#
#     @staticmethod
#     def maxOutputNumber() -> int:
#         return -1


export = [ToNumericOp, ToCategoricalOp]
