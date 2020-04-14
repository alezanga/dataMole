import pandas as pd
from data_preprocessor.data import Saver


class CsvSaver(Saver):
    def write(self, df, **kwargs):
        df._Frame__df.to_csv(**kwargs)
