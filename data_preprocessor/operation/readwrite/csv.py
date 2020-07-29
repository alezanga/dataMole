from typing import Iterable, List, Dict, Set

import pandas as pd
from PySide2.QtCore import Slot

from data_preprocessor import data, exceptions as exp
from data_preprocessor.gui.editor import OptionsEditorFactory, AbsOperationEditor
from data_preprocessor.gui.editor.loaders import LoadCSVEditor
from data_preprocessor.operation.interface.operation import Operation


class CsvLoader(Operation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__file: str = None
        self.__separator: str = None
        self.__wName: str = None
        self.__splitByRowN: int = None
        self.__selectedColumns: Set[int] = set()

    def hasOptions(self) -> bool:
        return self.__file is not None and self.__separator is not None and self.__wName

    def execute(self) -> None:
        if not self.hasOptions():
            raise exp.InvalidOptions('Options are not set')
        pd_df = pd.read_csv(self.__file, sep=self.__separator,
                            index_col=False,
                            usecols=self.__selectedColumns,
                            chunksize=self.__splitByRowN)
        if self.__splitByRowN is not None:
            # pd_df is a chunk iterator
            for i, chunk in enumerate(pd_df):
                name: str = self.__wName + '_{:d}'.format(i)
                self._workbench.setDataframeByName(name, data.Frame(chunk))
                # TOCHECK: this does not set a parent for the FrameModel (since workbench lives in
                #  different thread)
        else:
            # entire dataframe is read
            self._workbench.setDataframeByName(self.__wName, data.Frame(pd_df))

    @staticmethod
    def name() -> str:
        return 'Load CSV'

    @staticmethod
    def shortDescription() -> str:
        return 'Loads a dataframe from a CSV'

    def longDescription(self) -> str:
        return 'By selecting \'Split by rows\' you can load a CSV file as multiple smaller dataframes ' \
               'each one with the specified number of rows. This allows to load big files which are ' \
               'too memory consuming to load with pandas'

    def setOptions(self, file: str, separator: str, name: str, splitByRow: int,
                   selectedCols: Set[int]) -> None:
        errors = list()
        if not name:
            errors.append(('nameError', 'Error: a valid name must be specified'))
        if not selectedCols:
            errors.append(('noSelection', 'Error: at least 1 attribute must be selected'))
        if errors:
            raise exp.OptionValidationError(errors)
        self.__file = file
        self.__separator = separator
        self.__wName = name
        self.__splitByRowN = splitByRow if (splitByRow and splitByRow > 0) else None
        self.__selectedColumns = selectedCols

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return self.__file, self.__separator, self.__wName, self.__splitByRowN, self.__selectedColumns

    def getEditor(self) -> 'AbsOperationEditor':
        return LoadCSVEditor()


class CsvWriter(Operation):
    def __init__(self, frameName: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__frame_name: str = frameName
        self.__path: str = None
        self.__sep: str = ','
        self.__nan_rep: str = 'nan'
        self.__float_format: str = '%g'
        self.__header: bool = True
        self.__index: bool = True
        self.__selected_columns: List[str] = list()
        self.__date_format: str = '%Y-%m-%d %H:%M:%S'
        self.__decimal: str = '.'

    def execute(self) -> None:
        df: pd.DataFrame = self._workbench.getDataframeModelByName(self.__frame_name).frame.getRawFrame()
        df.to_csv(self.__path, sep=self.__sep, na_rep=self.__nan_rep,
                  float_format=self.__float_format, columns=self.__selected_columns,
                  header=self.__header, index=self.__index, date_format=self.__date_format,
                  decimal=self.__decimal)

    @staticmethod
    def shortDescription() -> str:
        return 'Load a dataframe from CSV file'

    def getEditor(self) -> 'AbsOperationEditor':
        factory = OptionsEditorFactory()
        factory.initEditor(subclass=WriteEditorBase)
        factory.withComboBox('Frame to write', 'frame', False, model=self.workbench)
        factory.withFileChooser(key='file', label='Choose a file', extensions='Csv (*.csv)', mode='save')
        factory.withAttributeTable(key='sele', checkbox=True, nameEditable=False, showTypes=True,
                                   options=None, types=self.acceptedTypes())
        factory.withTextField('Separator', 'sep')
        factory.withTextField('Nan repr', 'nan')
        factory.withTextField('Float format', 'ffloat')
        factory.withTextField('Decimal', 'decimal')
        factory.withCheckBox('Write column names', 'header')
        factory.withCheckBox('Write index values', 'index')
        factory.withComboBox('Datetime format', 'date', True, strings=['%Y-%m-%d %H:%M:%S',
                                                                       '%Y-%m-%d', '%H:%M:%S'])
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        # Make editor react to frame change
        editor.frame.currentTextChanged.connect(editor.inputFrameChanged)
        ct = editor.frame.currentText()
        if ct:
            editor.inputFrameChanged(ct)

    def setOptions(self, frame: str, file: str, sele: Dict[int, None], sep: str, nan: str, ffloat: str,
                   decimal: str, header: bool, index: bool, date: str) -> None:
        errors = list()
        if frame not in self.workbench.names:
            errors.append(('e1', 'Error: frame name is not valid'))
        if not sele:
            errors.append(('e2', 'Error: no attribute to write are selected'))
        nan = parseUnicodeStr(nan)
        sep = parseUnicodeStr(sep)
        if not sep:
            errors.append(('es1', 'Error: a separator char is required'))
        elif len(sep) > 1:
            errors.append(('es2', 'Error: separator must be a single character'))
        if not decimal:
            errors.append(('na1', 'Error: a decimal separator is required'))
        elif len(decimal) > 1:
            errors.append(('na2', 'Error: decimal separator must be a single character'))
        if not date:
            errors.append(('d1', 'Error: datetime format must be specified'))
        if not file:
            errors.append(('f1', 'Error: no output file specified'))
        if errors:
            raise exp.OptionValidationError(errors)

        # Save selected column names
        columns: List[str] = self.workbench.getDataframeModelByName(frame).frame.colnames

        self.__frame_name = frame
        self.__path = file
        self.__selected_columns = [columns[i] for i in sele.keys()]
        self.__date_format = date
        self.__sep = sep
        self.__nan_rep = nan
        self.__float_format = ffloat
        self.__decimal = decimal
        self.__index = index
        self.__header = header

    def getOptions(self) -> Iterable:
        return {
            'frame': self.__frame_name,
            'file': self.__path,
            'sele': {i: None for i in self.__selected_columns},
            'date': self.__date_format,
            'sep': self.__sep,
            'nan': self.__nan_rep,
            'ffloat': self.__float_format,
            'decimal': self.__decimal,
            'header': self.__header,
            'index': self.__index
        }

    def needsOptions(self) -> bool:
        return True


def parseUnicodeStr(s: str) -> str:
    return bytes(s, 'utf-8').decode('unicode_escape')


class WriteEditorBase(AbsOperationEditor):
    @Slot(str)
    def inputFrameChanged(self, name: str) -> None:
        frame: 'FrameModel' = self.workbench.getDataframeModelByName(name)
        self.sele.setSourceFrameModel(frame)
