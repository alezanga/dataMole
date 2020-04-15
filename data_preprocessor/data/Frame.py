import pandas as pd
from typing import List, Union, Callable, Iterable, Dict
from data_preprocessor.data.type_dict import type_dict

from data_preprocessor.data.Shape import Shape


class Frame:
    """
    Interface for common dataframe operations
    """
    __df: pd.DataFrame = None

    def __init__(self, data: Union[pd.DataFrame, pd.Series, Iterable, Dict, None] = None):
        if isinstance(data, pd.DataFrame):
            self.__df: pd.DataFrame = data
        elif isinstance(data, pd.Series):
            self.__df: pd.DataFrame = data.to_frame()
        else:
            self.__df: pd.DataFrame = pd.DataFrame(data)

    def __getitem__(self, key):
        return Frame(self.__df.__getitem__(key))

    def __setitem__(self, key, value):
        if isinstance(value, Frame):
            self.__df.__setitem__(key, value.__df)
        else:
            self.__df.__setitem__(key, value)

    def __delitem__(self, key):
        self.__df.__delitem__(key)

    # def load(self, filename: str, header: int = 1, separator: str = ',', nan_values: List[str] = None,
    #          keep_def_nan: bool = True, decimal: str = '.'):
    #     self.__df = pd.read_csv(filename, sep=separator, header=header, na_values=nan_values,
    #                             keep_default_na=keep_def_nan, decimal=decimal)
    #
    # def save(self, filename: str, separator: str, extension: str):
    #     """
    #     Save a Frame to file
    #     :param filename:
    #     :param separator:
    #     :param extension:
    #     :return:
    #     """
    #     if extension == 'csv':
    #         self.__df.to_csv(filename, sep=separator)
    #     elif extension == 'arff':
    #         frame_to_arff(self.__df, **locals())
    #     else:
    #         raise ValueError('Format {} not accepted'.format(extension))

    @property
    def columns(self) -> List[Union[str, int]]:
        """
        Return headers of file
        :return:
        """
        return self.__df.columns.values.tolist()

    @columns.setter
    def columns(self, new_values: List[Union[str, int]]) -> None:
        """
        Set new names for columns
        :param new_values: a list of names
        """
        if len(self.columns) != len(new_values):
            raise ValueError('List of names must match the number of columns')
        self.__df.columns = new_values

    def apply(self, fn: Callable) -> 'Frame':
        """
        Apply a function to each row of the dataset
        :param fn: function to apply
        :return: a new Frame to which fn was applied
        """
        return Frame(self.__df.apply(axis=1, func=fn))

    def query(self, expr: str) -> 'Frame':
        return Frame(self.__df.query(expr, inplace=False))

    def set_index(self, col: Union[str, int]) -> 'Frame':
        return Frame(self.__df.set_index(col))

    def drop_nan(self, axis: int):
        return Frame(self.__df.dropna(axis=axis))

    def head(self, n: int = 10) -> 'Frame':
        return Frame(self.__df.head(n))

    def drop(self, cols: Union[str, Iterable], index: int) -> 'Frame':
        return Frame(self.__df.drop(labels=cols, index=index, inplace=False))

    def duplicated(self, cols: Union[str, Iterable]) -> List[bool]:
        """
        Boolean list with duplicates rows
        :param cols:
        :return:
        """

    def to_dict(self) -> Dict[str, List]:
        return self.__df.to_dict(orient='list')

    @property
    def shape(self) -> Shape:
        """
        The shape of a Frame
        :return: Shape object
        """
        s = Shape()
        internal_sh = self.__df.shape
        # Set number of columns
        s.n_columns = internal_sh[1]

        # Set number of rows
        s.n_rows = internal_sh[0]

        # Set index column, or None if there is no index set (or the default one)
        s.index = self.__df.index.name if self.__df.index.name else None

        # Set a dict with column names and respective types
        # Types are set in a more readable format using type_dict to convert names
        s.col_name_type = dict()
        for col, type_val in self.__df.dtypes.items():
            s.col_name_type[col] = type_dict.get(type_val.name, type_val.name)

        # If index is a column of the dataframe add also its name and type
        if s.index:
            type_val = self.__df.index.dtype.name
            s.col_name_type[s.index] = type_dict.get(type_val, type_val)

        return s
