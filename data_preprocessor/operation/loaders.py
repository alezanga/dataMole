from typing import Iterable, Union, List

import pandas as pd

from data_preprocessor import data
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.operation.interface.graph import InputGraphOperation
from .interface.exceptions import InvalidOptions, OptionValidationError
from ..gui.editor.loaders import LoadCSVEditor


class CsvLoader(InputGraphOperation):
    def __init__(self, w):
        super().__init__(w)
        self.__file: str = None
        self.__separator: str = None
        self.__wName: str = None
        self.__splitByRowN: int = None
        self.__selectedColumns: List[int] = list()

    def hasOptions(self) -> bool:
        return self.__file is not None and self.__separator is not None and self.__wName

    def getOutputShape(self) -> Union[data.Shape, None]:
        return None

    def execute(self) -> None:
        if not self.hasOptions():
            raise InvalidOptions('Options are not set')
        pd_df = pd.read_csv(self.__file, sep=self.__separator,
                            index_col=False,
                            usecols=self.__selectedColumns,
                            chunksize=self.__splitByRowN)
        if self.__splitByRowN is not None:
            # pd_df is a chunk iterator
            for i, chunk in enumerate(pd_df):
                name: str = self.__wName + '_{:d}'.format(i)
                self._workbench.appendNewRow(name, data.Frame(chunk))
                # TOCHECK: this does not set a parent for the FrameModel (since workbench lives in
                #  different thread)
        else:
            # entire dataframe is read
            self._workbench.appendNewRow(self.__wName, data.Frame(pd_df))

    @staticmethod
    def name() -> str:
        return 'Load CSV'

    def shortDescription(self) -> str:
        return 'Loads a dataframe from a CSV'

    def longDescription(self) -> str:
        return 'By selecting \'Split by rows\' you can load a CSV file as multiple smaller dataframes ' \
               'each one with the specified number of rows. This allows to load big files which are ' \
               'too memory consuming to load with pandas'

    def setOptions(self, file: str, separator: str, name: str, splitByRow: int,
                   selectedCols: List[int]) -> None:
        errors = list()
        if not name:
            errors.append(('nameError', 'Error: a valid name must be specified'))
        if not selectedCols:
            errors.append(('noSelection', 'Error: at least 1 attribute must be selected'))
        if errors:
            raise OptionValidationError(errors)
        self.__file = file
        self.__separator = separator
        self.__wName = name
        self.__splitByRowN = splitByRow if (splitByRow and splitByRow > 0) else None
        self.__selectedColumns = selectedCols

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return self.__file, self.__separator, self.__wName, self.__splitByRowN, self.__selectedColumns

    def getEditor(self) -> AbsOperationEditor:
        return LoadCSVEditor()
