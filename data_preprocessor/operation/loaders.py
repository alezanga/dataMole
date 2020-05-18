from typing import Iterable, Union

import pandas as pd

from data_preprocessor import data
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.operation.interface import InputGraphOperation, InvalidOption
from ..gui.editor.loaders import LoadCSVEditor


class CsvLoader(InputGraphOperation):
    def __init__(self, w):
        super().__init__(w)
        self.__file: str = None
        self.__separator: str = None

    def hasOptions(self) -> bool:
        return self.__file is not None and self.__separator is not None

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions():
            return None
        else:
            return self.execute().shape

    def execute(self) -> data.Frame:
        if not self.hasOptions():
            raise InvalidOption('Options are not set')
        pd_df = pd.read_csv(self.__file, sep=self.__separator)
        return data.Frame(pd_df)

    @staticmethod
    def name() -> str:
        return 'Load CSV'

    def shortDescription(self) -> str:
        return 'This command loads a dataframe from a CSV'

    def setOptions(self, file: str, separator: str) -> None:
        self.__file = file
        self.__separator = separator

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return self.__file, self.__separator

    def getEditor(self) -> AbsOperationEditor:
        return LoadCSVEditor()
