import pandas as pd
from data_preprocessor.data import Loader, Frame


class CsvLoader(Loader):
    def read(self, **kwargs) -> 'Frame':
        return Frame(pd.read_csv(**kwargs))
