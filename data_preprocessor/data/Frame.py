from typing import List, Union, Callable, Iterable, Dict, Any, Optional, Tuple

import pandas as pd

from data_preprocessor.data.Shape import Shape
from data_preprocessor.data.types import type_dict, inv_type_dict


class Frame:
    """
    Interface for common dataframe operations
    """

    def __init__(self, data: Union[pd.DataFrame, pd.Series, Iterable, Dict, None] = None,
                 empty: bool = False):
        if isinstance(data, pd.DataFrame):
            self.__df: pd.DataFrame = data
        elif isinstance(data, pd.Series):
            self.__df: pd.DataFrame = data.to_frame()
        else:
            self.__df: pd.DataFrame = pd.DataFrame(data)
        self.__empty: bool = True if data is None else empty

    def getRawFrame(self) -> pd.DataFrame:
        return self.__df

    def isEmpty(self) -> bool:
        """ Whether the Frame is to be considered empty (no rows) """
        return self.__empty

    @staticmethod
    def fromShape(s: Shape) -> 'Frame':
        columns = s.col_names
        types = s.col_types
        # index = [s.index] if s.has_index() else None

        data = dict()
        for n, t in zip(columns, types):
            data[n] = pd.Series([], dtype=inv_type_dict[t])

        df = pd.DataFrame(data)
        # Set name because pandas does not do it
        # df.index.name = s.index
        return Frame(df, empty=True)

    def at(self, e: Tuple[int, int]) -> Any:
        """ Get value of element at specified index

        :param e: tuple with exactly two element, the row and column index
        :return: element at specified index
        :raise ValueError: if the tuple has an invalid number of arguments (!= 2)
        """
        if len(e) != 2:
            raise ValueError('Function \'at\' must receive exactly 2 indices')
        return self.__df.iloc[e[0], e[1]]

    def columnsAt(self, cols: Union[List[int], List[str], int, str, slice]) -> 'Frame':
        """ Return a frame with only specified columns and the same number of rows

        :param cols: the columns to keep, by index or name
        :return: the frame with specified columns only
        :raise ValueError: if the 'cols' parameter has an invalid value
        """
        if not cols:
            raise ValueError('\'cols\' is not a valid object')
        if (isinstance(cols, list) and isinstance(cols[0], int)) or isinstance(cols, int):
            # cols: List[int] | int
            return Frame(self.__df.iloc[:, cols])
        elif (isinstance(cols, list) and isinstance(cols[0], str)) or isinstance(cols, str):
            # cols: List[str] | str
            return Frame(self.__df.loc[:, cols])
        elif isinstance(cols, slice):
            if (cols.stop and isinstance(cols.stop, int)) or (cols.start and isinstance(cols.start,
                                                                                        int)):
                # slice of ints
                return Frame(self.__df.iloc[:, cols])
            elif (cols.stop and isinstance(cols.stop, str)) or (cols.start and isinstance(cols.start,
                                                                                          str)):
                return Frame(self.__df.loc[:, cols])
            else:
                raise ValueError('Illegal slice of type: {}'.format(type(cols.stop)))
        else:
            raise TypeError('Illegal argument \'cols\' of type: {}'.format(type(cols)))

    def rowsAt(self, rows: Union[List[int], int, slice]) -> 'Frame':
        """ Get a frame with specified rows by their positional index. Doesn't change the number of
        columns

        :param rows: a list of integer indices, a single one or a slice
        :return: the frame with specified rows only
        :raise ValueError: if the argument has an illegal value
        """
        if not rows:
            raise ValueError('\'rows\' is an invalid object')
        if (isinstance(rows, list) and isinstance(rows[0], int)) or isinstance(rows, int):
            # rows: List[int] | int
            return Frame(self.__df.iloc[rows, :])
        elif isinstance(rows, slice) \
                and ((rows.stop and isinstance(rows.stop, int)) or (
                rows.start and isinstance(rows.start, int))):
            # rows is a slice of ints
            return Frame(self.__df.iloc[rows, :])
        else:
            raise TypeError('Illegal argument \'rows\' of type: {}'.format(type(rows)))

    def rowsAtIndex(self, rows: Union[List, Any, slice]) -> 'Frame':
        """ Get a frame with only specified rows selecting them by the dataframe index, leaving the
        columns unchanged

        :param rows: a list of indices, a single index or a slice with indexes
        :return: the frame object with specified rows
        :raise ValueError: if the parameter is an invalid object
        """
        if not rows:
            raise ValueError('\'rows\' is an invalid object')
        return Frame(self.__df.loc[rows, :])

    # def __getitem__(self, key) -> 'Frame':
    #     if isinstance(key[0], int):
    #         print(self.__df.iloc[key])
    #         return Frame(self.__df.iloc[key])
    #     elif isinstance(key[0], str):
    #         return Frame(self.__df.loc[key])
    #
    #     return Frame(self.__df.__getitem__(key))

    def __setitem__(self, key, value):
        if isinstance(value, Frame):
            self.__df.__setitem__(key, value.__df)
        else:
            self.__df.__setitem__(key, value)

    def __delitem__(self, key):
        self.__df.__delitem__(key)

    def __eq__(self, other: 'Frame') -> bool:
        return self.__df.equals(other.__df)

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

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
    def colnames(self) -> List[str]:
        """ The column names of the frame

        :return: the column names as a list
        """
        return self.__df.columns.values.tolist()

    def rename(self, new_values: Union[Dict[str, str], List[str]]) -> 'Frame':
        """ Set new names for columns

        :param new_values: a list of names if all columns should be renamed or a dict
        :return: a frame with renamed columns
        """
        if isinstance(new_values, dict):
            return Frame(self.__df.rename(columns=new_values, inplace=False))
        elif isinstance(new_values, list) and len(self.colnames) == len(new_values):
            new_df = self.__df.copy(deep=False)
            new_df.columns = new_values
            return Frame(new_df)
        else:
            raise ValueError('Wrong input argument for rename function')

    @property
    def index(self) -> List:
        """ Return the row indices as a list of values """
        return self.__df.index.tolist()

    def setIndex(self, col: Union[str, int]) -> 'Frame':
        """
        Sets index of the dataframe

        :param col: the column number or name
        :return: a new frame with the new index
        """
        if isinstance(col, int):
            d = self.__df.set_index(self.__df.columns[col], drop=False, inplace=False)
            d.index.name = self.__df.columns[col]
            return Frame(d)
        else:
            d = self.__df.set_index(col, drop=False, inplace=False)
            d.index.name = col
            return Frame(d)

    # def addRow(self):

    def apply(self, fn: Callable) -> 'Frame':
        """ Apply a function to each row of the dataset

        :param fn: function to apply
        :return: a new Frame to which fn was applied
        """
        return Frame(self.__df.apply(axis=1, func=fn))

    def query(self, expr: str) -> 'Frame':
        """ Select rows where 'expr' condition evaluates to true

        :param expr: boolean expression
        :return: a frame with a subset of rows and same number of columns
        """
        return Frame(self.__df.query(expr, inplace=False))

    def drop_nan(self, axis: int):
        return Frame(self.__df.dropna(axis=axis))

    def head(self, n: int = 10) -> pd.DataFrame:
        return self.__df.head(n)

    def dropCols(self, cols: Union[int, str, List[int], List[str]]) -> 'Frame':
        """ Remove columns from a dataframe

        :param cols: a single label or a list
        :return: a new dataframe with removed columns
        """
        if isinstance(cols, int) or (isinstance(cols, list) and isinstance(cols[0], int)):
            return Frame(self.__df.drop(columns=self.__df.columns[cols], inplace=False))
        return Frame(self.__df.drop(columns=cols, inplace=False))

    def dropRows(self, rows: Union[List, Any, int], by: str = 'index') -> 'Frame':
        """ Remove rows from dataframe

        :param rows: rows to remove as a list of indices, row numbers or a single item
        :param by: one of 'index' or 'number'
        :raise ValueError: if the 'by' is not recognised
        :return: the new frame with removed rows
        """
        if by == 'index':
            return Frame(self.__df.drop(index=rows, inplace=False))
        elif by == 'number':
            return Frame(self.__df.drop(index=self.__df.index[rows], inplace=False))
        else:
            raise ValueError('\'by\' parameter must be set to \'index\' or \'number\'')

    def replace(self, replacing: Union[List, Any, Dict], new_value: Optional[Any] = None) -> 'Frame':
        """ Replace one or more values in the whole dataframe

        :param replacing: a single value, a list of values or a dictionary saying what to replace for
            each value
        :param new_value: the value to substitute. If 'replacing' is a dictionary it must be None
        :return: the new frame with replaced values
        :raise ValueError: if the supplied parameters are not valid
        """
        if not replacing:
            raise ValueError('\'replacing\' parameter cannot be invalid')
        elif isinstance(replacing, dict) and not new_value:
            return Frame(self.__df.replace(to_replace=replacing, value=None, inplace=False))
        elif new_value:
            return Frame(self.__df.replace(to_replace=replacing, value=new_value, inplace=False))
        else:
            raise ValueError('\'replacing\' must be a List, Dict or a scalar. If it is a dict '
                             '\'values\' must be None')

    def replaceRegex(self, regex: Union[List[str], str, Dict[str, Any]], new_value: Any) -> 'Frame':
        """ Replace a string pattern in the whole dataframe. Works only on values of type string

        :param regex: a single regex, a list of regex or a dictionary saying what to replace for each
            regex
        :param new_value: the value to substitute. If 'regex' is a dictionary it must be None
        :return: the new frame with replaced values
        :raise ValueError: if the supplied parameters are not valid
        """
        if not regex:
            raise ValueError('\'regex\' parameter cannot be invalid')
        elif isinstance(regex, dict) and not new_value:
            return Frame(self.__df.replace(to_replace=None, regex=regex, value=None))
        elif new_value:
            return Frame(self.__df.replace(to_replace=None, regex=regex, value=new_value))
        else:
            raise ValueError('\'regex\' must be a single string regular expression, or a list or dict. '
                             'If it is a dict \'values\' must be None')

    def mean(self, column: str) -> float:
        a = self.columnsAt(column).__df
        if a.dtypes[0].name == 'int64' or a.dtypes[0].name == 'float64':
            return self.columnsAt(column).__df.mean(axis=0, numeric_only=True)[column]
        else:
            raise TypeError('Only numeric columns can be used for mean')

    def std(self, column: str) -> float:
        a = self.columnsAt(column).__df
        if a.dtypes[0].name == 'int64' or a.dtypes[0].name == 'float64':
            return self.columnsAt(column).__df.std(axis=0, numeric_only=True)[column]
        else:
            raise TypeError('Only numeric columns can be used for standard deviation')

    def addColumn(self, name: str) -> 'Frame':
        f = self.__df.copy()
        f[name] = ''
        return Frame(f)

    def duplicated(self, cols: Union[str, Iterable]) -> List[bool]:
        """ Boolean list with duplicates rows

        :param cols:
        :return:
        """
        pass

    def to_dict(self) -> Dict[str, List]:
        return self.__df.to_dict(orient='list')

    @property
    def shape(self) -> Shape:
        """ The shape of a Frame

        :return: Shape object
        """
        s = Shape()
        internal_sh = self.__df.shape

        # Set number of columns
        s.n_columns = internal_sh[1]

        # Set number of rows
        s.n_rows = internal_sh[0] if not self.isEmpty() else 0

        # Set index column, or None if there is no index set (or the default one)
        s.index = self.__df.index.name if self.__df.index.name else None

        # Types are set in a more readable format using type_dict to convert names
        s.col_names = list()
        s.col_types = list()
        # s.numeric_types = list()
        for col, type_val in self.__df.dtypes.items():
            pretty_type = type_dict.get(type_val.name, type_val.name)
            s.col_names.append(col)
            s.col_types.append(pretty_type)
            # if pretty_type == 'int' or pretty_type == 'float':
            #     s.numeric_types.append(len(s.col_types) - 1)

        # If index is a column of the dataframe add also its name and type
        # if s.index:
        # type_val = self.__df.index.dtype.name
        # s.col_names.append(s.index)
        # s.col_types.append(type_dict.get(type_val, type_val))

        return s
