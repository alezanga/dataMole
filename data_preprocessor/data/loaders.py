import abc

import pandas as pd

from data_preprocessor.data import Frame


class Loader(abc.ABC):
    @abc.abstractmethod
    def read(self, **kwargs) -> Frame:
        pass


class CsvLoader(Loader):
    def read(self, **kwargs) -> Frame:
        return Frame(pd.read_csv(**kwargs))

