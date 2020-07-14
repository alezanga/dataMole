from typing import Dict, Any, Union, Optional

import pandas as pd
import prettytable as pt

from data_preprocessor import data
from data_preprocessor.data.types import Types, Categorical
from data_preprocessor.exceptions import OptionValidationError
from data_preprocessor.flogging import Loggable
from data_preprocessor.gui.editor import AbsOperationEditor, OptionsEditorFactory, \
    OptionValidatorDelegate
from data_preprocessor.gui.mainmodels import FrameModel
from data_preprocessor.operation.interface.graph import GraphOperation
from data_preprocessor.operation.utils import SingleStringValidator, isFloat


class FillNan(GraphOperation, Loggable):
    _DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # List of selected attributes to fill
        self.__selection: Dict[int, Union[str, float, pd.Timestamp]] = dict()
        self.__method: str = None  # { bfill, ffill, mean }
        self.__byValue: bool = True  # Use values or method

    def logOptions(self) -> str:
        columns = self.shapes[0].colNames
        strings = ['Method: {}'.format(self.__method) if not self.__byValue else 'value']
        if self.__byValue:
            tt = pt.PrettyTable(field_names=['Column', 'Fill value'])
            for i, v in self.__selection.items():
                strV = str(v) if not isinstance(v, pd.Timestamp) else v.strftime(self._DATE_FORMAT)
                tt.add_row([columns[i], strV])
        else:
            tt = pt.PrettyTable(field_names=['Columns'])
            for i, v in self.__selection.items():
                tt.add_row([columns[i]])
        strings.append(tt.get_string(border=True, vrules=pt.ALL))
        return '\n'.join(strings)

    def __logExecution(self, valDict: Dict[str, Union[float, pd.Timestamp]]) -> None:
        strings = ['Computed mean values for column:']
        tt = pt.PrettyTable(field_names=['Column', 'Mean'], print_empty=False)
        for c, val in valDict.items():
            strVal = val.strftime(self._DATE_FORMAT) if isinstance(val, pd.Timestamp) \
                else '{:G}'.format(val)
            tt.add_row([c, strVal])
        strings.append(tt.get_string(border=True, vrules=pt.ALL))
        self._logExecutionString = '\n'.join(strings)

    def execute(self, df: data.Frame) -> data.Frame:
        columns = df.colnames
        rdf = df.getRawFrame().copy(True)
        processDf = rdf.iloc[:, list(self.__selection.keys())]
        if self.__byValue:
            valueDict = {columns[k]: v for k, v in self.__selection.items()}
            processed = processDf.fillna(valueDict, axis=0)
        elif self.__method == 'mean':
            # For some reason pandas can't compute mean of a dataframe so I do it by hand
            valueDict = {k: processDf[k].mean() for k in processDf}
            # This is the only case where we need an execution log
            self.__logExecution(valueDict)
            processed = processDf.fillna(valueDict, axis=0)
        else:
            processed = processDf.fillna(method=self.__method, axis=0)
        # Merge result with previous frame, keeping column order
        processed = pd.concat([processed, rdf.drop(processed.columns.values, axis=1)], axis=1,
                              ignore_index=False)[columns]
        return data.Frame(processed)

    @staticmethod
    def name() -> str:
        return 'FillNan'

    def shortDescription(self) -> str:
        return 'Fill NaN/NaT values over columns with specified method'

    def hasOptions(self) -> bool:
        return bool(self.__selection and self.__method)

    def unsetOptions(self) -> None:
        self.__selection = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Dict[str, Any]:
        selection = dict()
        if not self.__byValue:
            selection = {k: None for k in self.__selection.keys()}
        else:
            for k, val in self.__selection.items():
                strVal = str(val) if not isinstance(val, pd.Timestamp) else val.strftime(
                    format=self._DATE_FORMAT)
                selection[k] = {'fill': strVal}
        return {'selected': selection,
                'fillMode': self.__method if not self.__byValue else 'value'}

    def setOptions(self, selected: Dict[int, Dict[str, str]], fillMode: str) -> None:
        withValue = fillMode == 'value'
        errors = list()
        if not selected:
            errors.append(('noSelection', 'Error: no attributes have been selected'))
        if not fillMode:
            errors.append(('noMode', 'Error: no fill method has been chosen'))
        if any(map(lambda i: self.shapes[0].colTypes[i] == Types.String or
                             isinstance(self.shapes[0].colTypes[i], Categorical),
                   selected.keys())) and (withValue or fillMode == 'mean'):
            errors.append(('strVal', 'Error: "Mean" and "Value" methods are only supported when all '
                                     'selected attributes are of type Numeric/Datetime'))
        if errors:
            raise OptionValidationError(errors)
        selectedDict: Dict[int, Any] = dict()
        if withValue:
            # Process each value to replace
            for k, opts in selected.items():
                val = opts.get('fill', None)
                if not val:
                    # If value is not set, but replace is by value
                    errors.append(('noVal', 'Error: fill value is not set at row {}'.format(k)))
                else:
                    valType = self.shapes[0].colTypes[k]
                    if valType == Types.Numeric:
                        if isFloat(val):
                            val = float(val)
                        else:
                            errors.append(
                                ('valType',
                                 'Error: row {:d} has numeric type, but inserted value {:s} is not'.format(
                                     k, val)))
                    elif valType == Types.Datetime:
                        ts = pd.to_datetime(val, format=self._DATE_FORMAT, errors='coerce')
                        if pd.isna(ts):
                            errors.append(('timeF', 'Error: invalid datetime format at row {:d}. Format '
                                                    'should be: yyyy-mm-dd hh:mm:ss'.format(k)))
                        else:
                            val = ts
                    selectedDict[k] = val
                if len(errors) > 8:
                    # Don't stack too many errors
                    break
        else:
            # Value column is not relevant
            selectedDict = {k: None for k in selected.keys()}
        if errors:
            raise OptionValidationError(errors)
        # Set options
        self.__method = fillMode
        self.__selection = selectedDict
        self.__byValue = withValue

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable(key='selected', checkbox=True, nameEditable=False,
                                   showTypes=True, types=self.acceptedTypes(),
                                   options={
                                       'fill': ('Fill value',
                                                OptionValidatorDelegate(SingleStringValidator()), None)
                                   })
        factory.withRadioGroup(key='fillMode', label='Method',
                               values=[('Backfill', 'bfill'),
                                       ('Pad', 'ffill'),
                                       ('Mean', 'mean'),
                                       ('Values', 'value')])
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.inputShapes = self.shapes
        editor.workbench = self.workbench
        # Connect and set frame
        editor.selected.setSourceFrameModel(FrameModel(editor, self.shapes[0]))

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions():
            return None
        return self.shapes[0]

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


export = FillNan
