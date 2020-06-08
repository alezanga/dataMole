from typing import Iterable, List, Any, Tuple, Dict, Optional

import numpy as np
from PySide2.QtWidgets import QHeaderView

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.gui.frame import FrameModel
from data_preprocessor.gui.generic.OptionsEditorFactory import OptionsEditorFactory
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.graph import GraphOperation
from data_preprocessor.operation.utils import ManyMixedListsValidator, MixedListValidator, splitList, \
    parseNan, joinList


def isValidFloat(x):
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True


def floatList(values: List, invalid: str) -> List:
    """
    Converts a list of values into float values if possible.

    :param values: values to convert
    :param invalid: {'drop', 'nan', 'ignore'}.
        - 'drop': invalid float values are dropped
        - 'nan': invalid floats are set to np.nan
        - 'ignore': invalid values are left untouched. May results in a list of mixed type
    :return: if invalid is 'drop' or 'nan' returns a list of floats, otherwise it may return a
        list of mixed type
    """
    floatValues = list()
    for el in values:
        if isValidFloat(el):
            floatValues.append(float(el))
        elif invalid == 'ignore':
            floatValues.append(el)
        elif invalid == 'nan':
            floatValues.append(np.nan)
    return floatValues


class MergeValuesOp(GraphOperation):
    """ Merge values of one attribute into a single value """
    Nan = np.nan

    def __init__(self):
        super().__init__()
        # { col: ([ [vala1, vala2], [valb1, valb2] ], [replacea, replaceb])}
        self.__attributes: Dict[int, Tuple[List[List], List[Any]]] = dict()
        self.__invertedReplace: bool = False
        # self.__attribute: int = None
        # self.__values_to_merge: List = list()
        # self.__merge_val: Any = None

    def execute(self, df: data.Frame) -> data.Frame:
        pd_df = df.getRawFrame().copy(True)
        for c, colOptions in self.__attributes.items():
            for valueList, replaceVal in zip(*colOptions):
                if self.__invertedReplace:
                    valuesToReplace: List = pd_df.iloc[:, c].unique().tolist()
                    for a in valueList:
                        try:
                            valuesToReplace.remove(a)
                        except ValueError:
                            pass  # Value not in list (ignore)
                else:
                    valuesToReplace = valueList
                pd_df.iloc[:, c] = pd_df.iloc[:, c].replace(to_replace=valuesToReplace,
                                                            value=replaceVal,
                                                            inplace=False)
        return data.Frame(pd_df)

    def getOutputShape(self) -> Optional[data.Shape]:
        if self.hasOptions() and self.shapes[0] is not None:
            return self.shapes[0]
        return None

    @staticmethod
    def name() -> str:
        return 'Merge values'

    def shortDescription(self) -> str:
        return 'Substitute all specified values in a attribute and substitute them with a single value'

    def acceptedTypes(self) -> List[Types]:
        return [Types.String, Types.Categorical, Types.Numeric]

    def setOptions(self, table: Dict[int, Dict[str, str]], inverted: bool) -> None:
        if not table:
            raise OptionValidationError([('nooptions', 'Error: options are not set for any attribute')])
        options: Dict[int, Tuple[List[List], List]] = dict()
        for c, opt in table.items():
            type_c = self.shapes[0].col_types[c]
            values: str = opt.get('values', None)
            replace: str = opt.get('replace', None)
            if not values or not replace:
                raise OptionValidationError(
                    [('incompleteoptions', 'Error: options are not set at row {:d}'.format(c))])
            lists: List[str] = splitList(values, ';')
            replace: List[str] = splitList(replace, ';')
            if not lists or not replace:
                raise OptionValidationError([('incompleteoptions', 'Error: options are not set at row '
                                                                   '{:d}'.format(c))])
            if len(lists) != len(replace):
                raise OptionValidationError([('wrongnum', 'Error: number of intervals is not equal to '
                                                          'the number of values to replace at row {:d}'
                                              .format(c))])
            parsedValues: List[List[str]] = [splitList(s, ' ') for s in lists]
            if type_c == Types.Numeric:
                if not all(map(isValidFloat, replace)):
                    err = ('numericinvalid', 'Error: list of values to replace contains non '
                                             'numeric value at row {}, but selected attribute '
                                             'is numeric'.format(c))
                    raise OptionValidationError([err])
                replace: List[float] = [float(x) for x in replace]
                parsedValues: List[List[float]] = [floatList(l, invalid='drop') for l in parsedValues]
            else:
                # If type is not numeric everything will be treated as string
                replace: List = parseNan(replace)
                parsedValues: List[List] = [parseNan(a) for a in parsedValues]
            # Save parsed options for this column
            options[c] = (parsedValues, replace)
        self.__attributes = options
        self.__invertedReplace = inverted

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        options = dict()
        options['table'] = dict()
        for c, opt in self.__attributes.items():
            # Convert every internal list into a string separated by spaces
            s: List[str] = list(map(lambda x: joinList(x, sep=' '), opt[0]))
            options['table'][c] = {
                'values': joinList(s, sep='; '),
                'replace': joinList(opt[1], sep='; ')
            }
        options['inverted'] = self.__invertedReplace
        return options

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        options = {
            'values': ('Values', ManyMixedListsValidator()),
            'replace': ('Replace with', MixedListValidator())
        }
        factory.initEditor()
        factory.withAttributeTable('table', True, False, True, options, self.acceptedTypes())
        factory.withCheckBox('Invert values selection', 'inverted')
        e = factory.getEditor()
        # Set frame model
        e.table.setSourceFrameModel(FrameModel(e, self.shapes[0]))
        # Stretch new section
        e.table.tableView.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        e.table.tableView.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        return e

    def hasOptions(self) -> bool:
        return self.__attributes and self.__invertedReplace is not None

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


export = MergeValuesOp
