from typing import List, Union, Iterable, Dict, Optional, Tuple, Any

import numpy as np
import pandas as pd
import prettytable as pt
from PySide2.QtWidgets import QHeaderView, QItemEditorFactory, QStyledItemDelegate, QWidget
from pandas.api.types import CategoricalDtype

from data_preprocessor import data, flogging
from data_preprocessor import exceptions as exp
from data_preprocessor.data.types import Types, Type
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.graph import GraphOperation
from .utils import MixedListValidator, splitString, joinList, SingleStringValidator
from ..gui.editor.OptionsEditorFactory import OptionsEditorFactory, OptionValidatorDelegate
from ..gui.mainmodels import FrameModel


class ToNumericOp(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attributes: List[int] = list()
        self.__errorMode: str = 'raise'  # {'raise', 'coerce'}

    def hasOptions(self) -> bool:
        if self.__attributes:
            return True
        return False

    def logOptions(self) -> str:
        sc = self.shapes[0].colNames
        columns = [sc[i] for i in self.__attributes]
        tt = pt.PrettyTable(field_names=['Selected columns'])
        for col in columns:
            tt.add_row([col])
        tt.align = 'l'
        return tt.get_string(border=True, vrules=pt.ALL) + '\nError mode: {}'.format(
            self.__errorMode)

    def execute(self, df: data.Frame) -> data.Frame:
        # Deep copy
        raw_df = df.getRawFrame().copy(deep=True)
        allCols: List[str] = raw_df.columns.to_list()

        converted: Dict[str, np.ndarray] = dict()
        processedCols = list()
        for a in self.__attributes:
            view = raw_df.iloc[:, a]
            colName = allCols[a]
            converted[colName] = pd.to_numeric(view.values, errors=self.__errorMode, downcast='float')
            processedCols.append(colName)
        raw_df = raw_df.drop(columns=processedCols)
        # Get processed frame and set back its index
        processed = pd.DataFrame(converted).set_index(raw_df.index)
        raw_df = pd.concat([processed, raw_df], ignore_index=False, axis=1)[allCols]
        return data.Frame(raw_df)

    @staticmethod
    def name() -> str:
        return 'toNumeric'

    def shortDescription(self) -> str:
        return 'Convert one attribute to Numeric values. All types except Datetime can be converted'

    def acceptedTypes(self) -> List[Type]:
        return [Types.String, Types.Ordinal, Types.Nominal]

    def setOptions(self, attributes: Dict[int, Dict[str, str]], errors: str) -> None:
        err = list()
        if not attributes:
            err.append(('nooptions', 'Error: select at least one attribute'))
        if not errors:
            err.append(('Noerror', 'Error: error mode must be specified'))
        if err:
            raise exp.OptionValidationError(err)

        self.__attributes = list(attributes.keys())
        self.__errorMode = errors

    def unsetOptions(self) -> None:
        self.__attributes = list()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return {'attributes': {k: None for k in self.__attributes}, 'errors': self.__errorMode}

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True, options=None,
                                   types=self.acceptedTypes())
        factory.withRadioGroup(key='errors', label='Error mode',
                               values=[('Raise', 'raise'), ('Coerce', 'coerce')])
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.acceptedTypes = self.acceptedTypes()
        editor.inputShapes = self._shapes
        # Set frame model
        editor.attributes.setSourceFrameModel(FrameModel(editor, self.shapes[0]))

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions() or not self._shapes[0]:
            return None
        s = self._shapes[0].clone()
        for i in self.__attributes:
            s.colTypes[i] = Types.Numeric
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


class ToCategoricalOp(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attributes: Dict[int, Tuple[Optional[List[str]], bool]] = dict()

    def hasOptions(self) -> bool:
        if self.__attributes:
            return True
        return False

    def logOptions(self) -> str:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Column', 'Categories', 'Ordered'])
        tt.align = 'l'
        for a, opts in self.__attributes.items():
            cats = ', '.join(opts[0]) if opts[0] else 'All'
            tt.add_row([columns[a], cats, opts[1] if opts[1] is not None else False])
        return tt.get_string(border=True, vrules=pt.ALL)

    def execute(self, df: data.Frame) -> data.Frame:
        # Deep copy
        raw_df = df.getRawFrame().copy(deep=True)
        # To string
        columnIndexes = list(self.__attributes.keys())
        isNan = raw_df.iloc[:, columnIndexes].isnull()
        raw_df.iloc[:, columnIndexes] = raw_df.iloc[:, columnIndexes] \
            .astype(dtype=str, errors='raise')
        # Set to nan where values where nan
        raw_df.iloc[:, columnIndexes] = raw_df.iloc[:, columnIndexes].mask(isNan, np.nan)
        colNames = df.shape.colNames
        # To category
        conversions: Dict[str, CategoricalDtype] = dict([
            (lambda i, opts: (colNames[i], CategoricalDtype(categories=opts[0],  # can be None
                                                            ordered=opts[1])))(index, info)
            for index, info in self.__attributes.items()
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

    def acceptedTypes(self) -> List[Type]:
        return [Types.String, Types.Numeric, Types.Ordinal, Types.Nominal]

    def setOptions(self, attributes: Dict[int, Dict[str, Any]]) -> None:
        if not attributes:
            raise exp.OptionValidationError([('nooptions', 'Error: select at least one attribute')])
        options: Dict[int, Tuple[Optional[List[str]], bool]] = dict()
        for c, opt in attributes.items():
            catString: Optional[str] = opt.get('cat', None)
            categories: Optional[List[str]] = None
            orderCategories: Optional[bool] = opt.get('ordered', None)
            if catString:
                categories = splitString(catString, sep=' ')
                if not categories:
                    categories = None
            options[c] = (categories, orderCategories)
        # Options are correctly set
        self.__attributes = options

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        options: Dict[int, Dict[str, str]] = dict()
        for c, opts in self.__attributes.items():
            options[c] = {'cat': joinList(opts[0], sep=' ') if opts[0] else '',
                          'ordered': opts[1] if opts[1] else False}
        return {'attributes': options}

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True, {
            'cat': ('Categories', OptionValidatorDelegate(MixedListValidator()), None),
            'ordered': ('Ordered', BoolDelegate(), False)}, types=self.acceptedTypes())
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.acceptedTypes = self.acceptedTypes()
        editor.inputShapes = self._shapes
        # Set frame model
        editor.attributes.setSourceFrameModel(FrameModel(editor, self.shapes[0]))
        # Fixed width to bool column
        editor.attributes.tableView.horizontalHeader().resizeSection(4, 90)
        editor.attributes.tableView.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        # Stretch new section
        editor.attributes.tableView.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions() or not self._shapes[0]:
            return None
        s = self._shapes[0].clone()
        for i, opt in self.__attributes.items():
            s.colTypes[i] = Types.Ordinal if opt[1] is True else Types.Nominal
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


class BoolDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option, index) -> QWidget:
        return QItemEditorFactory.defaultFactory().createEditor(1, parent)

    def displayText(self, value: bool, locale) -> str:
        return 'True' if value else 'False'


class ToTimestamp(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attributes: Dict[int, Optional[str]] = dict()
        self.__errorMode: str = None  # {'raise', 'coerce'}

    def logOptions(self) -> str:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Column', 'Parse format'])
        for a, f in self.__attributes.items():
            tt.add_row([columns[a], f if f else 'Infer'])
        tt.align = 'l'
        return tt.get_string(border=True, vrules=pt.ALL) + '\nError mode: {}'.format(
            self.__errorMode)

    def execute(self, df: data.Frame) -> data.Frame:
        pdf = df.getRawFrame().copy(True)
        for attr, dateFormat in self.__attributes.items():
            pdf.iloc[:, attr] = pd.to_datetime(pdf.iloc[:, attr], errors=self.__errorMode,
                                               infer_datetime_format=True, format=dateFormat)
        return data.Frame(pdf)

    @staticmethod
    def name() -> str:
        return 'toDatetime'

    def acceptedTypes(self) -> List[Type]:
        return [Types.String]

    def shortDescription(self) -> str:
        return 'Convert columns to datetime objects. Custom format may be specified.'

    def longDescription(self) -> str:
        pass

    def hasOptions(self) -> bool:
        return self.__attributes and self.__errorMode is not None

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        options = dict()
        tableOptions = dict()
        for row, dateFormat in self.__attributes.items():
            tableOptions[row] = {'format': dateFormat if dateFormat else ''}
        options['attributes'] = tableOptions
        options['errors'] = self.__errorMode if self.__errorMode else 'raise'
        return options

    def setOptions(self, attributes: Dict[int, Dict[str, str]], errors: str) -> None:
        valErrors = list()
        if not attributes:
            valErrors.append(('noSelected', 'Error: no attributes are selected'))
        if not errors:
            valErrors.append(('noMode', 'Error: error modality must be selected'))
        if valErrors:
            raise exp.OptionValidationError(valErrors)
        # Set options
        for row, opts in attributes.items():
            f = opts.get('format', None)
            self.__attributes[row] = f if f else None
        self.__errorMode = errors

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        tableOptions = {'format': ('Format', OptionValidatorDelegate(SingleStringValidator()), 'auto')}
        factory.withAttributeTable('attributes', True, False, False, tableOptions, self.acceptedTypes())
        factory.withRadioGroup('Error mode:', 'errors',
                               [('Raise', 'raise'), ('Coerce', 'coerce')])
        return factory.getEditor()

    def injectEditor(self, editor: AbsOperationEditor) -> None:
        editor.acceptedTypes = self.acceptedTypes()
        editor.inputShapes = self._shapes
        # Set frame model
        editor.attributes.setSourceFrameModel(FrameModel(editor, self.shapes[0]))
        # Stretch new section
        editor.attributes.tableView.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions() or not self._shapes[0]:
            return None
        s: data.Shape = self._shapes[0].clone()
        for i in self.__attributes.keys():
            s.colTypes[i] = Types.Datetime
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


class ToString(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attributes: List[int] = list()

    def hasOptions(self) -> bool:
        if self.__attributes:
            return True
        return False

    def logOptions(self) -> str:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Columns'])
        tt.align = 'l'
        for a in self.__attributes:
            tt.add_row([columns[a]])
        return tt.get_string(border=True, vrules=pt.ALL)

    def execute(self, df: data.Frame) -> data.Frame:
        # Deep copy
        raw_df = df.getRawFrame().copy(deep=True)
        # To string
        isNan = raw_df.iloc[:, self.__attributes].isnull()
        processed = raw_df.iloc[:, self.__attributes].astype(dtype=str, errors='raise')
        # Set to nan where values where nan
        processed = processed.mask(isNan, np.nan)
        colNames = df.shape.colNames
        raw_df.iloc[:, self.__attributes] = processed
        return data.Frame(raw_df)

    @staticmethod
    def name() -> str:
        return 'toString'

    def shortDescription(self) -> str:
        return 'Convert a column of any type to string'

    def acceptedTypes(self) -> List[Type]:
        return [Types.Numeric, Types.Ordinal, Types.Nominal, Types.Datetime]

    def setOptions(self, attributes: Dict[int, None]) -> None:
        if not attributes:
            raise exp.OptionValidationError([('noopt', 'Error: select at least one attribute')])
        self.__attributes = list(attributes.keys())

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Dict[str, Dict[int, None]]:
        return {'attributes': {i: None for i in self.__attributes}}

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True, {}, types=self.acceptedTypes())
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.acceptedTypes = self.acceptedTypes()
        editor.inputShapes = self._shapes
        # Set frame model
        editor.attributes.setSourceFrameModel(FrameModel(editor, self.shapes[0]))

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions() or not self._shapes[0]:
            return None
        s = self._shapes[0].clone()
        for i in self.__attributes:
            s.colTypes[i] = Types.String
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


export = ToNumericOp, ToCategoricalOp, ToTimestamp, ToString
