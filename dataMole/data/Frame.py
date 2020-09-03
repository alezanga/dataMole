from typing import List, Union, Iterable, Dict

import numpy as np
import pandas as pd

from dataMole.data.Shape import Shape
from dataMole.data.types import Types, wrapperType, IndexType, Type

# Constants
_date = pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                  dtype='datetime64[ns]')
_ordinal = pd.Categorical(['1', '6', '1', '3', '9'], ordered=True)
_nominal = pd.Categorical(['1', '6', '1', '3', '9'], ordered=False)
_string = ['0.2', '1', 'some', np.nan, 'many']
_stringNoNan = ['0.2', '1', 'some', '12.1', 'many']
_numeric = [0.3, 1, 2, 7, 11.1]


def integerToFloat(df: pd.DataFrame) -> pd.DataFrame:
    """ Converts every integer column to float column """
    integerCols = df.select_dtypes(include=int).columns.to_list()
    if not integerCols:
        return df
    cdf = df.copy(True)
    d = cdf[integerCols].astype(np.float)
    cdf = cdf.drop(labels=integerCols, axis=1)
    # Concat is much faster than subset assignment
    r = pd.concat([cdf, d], axis=1)
    r = r[df.columns.to_list()]
    return r


class Frame:
    """
    Interface for common dataframe operations
    """

    def __init__(self, data: Union[pd.DataFrame, pd.Series, Iterable, Dict, None] = None):
        if isinstance(data, pd.DataFrame):
            self.__df: pd.DataFrame = data
        elif isinstance(data, pd.Series):
            self.__df: pd.DataFrame = data.to_frame()
        else:
            self.__df: pd.DataFrame = pd.DataFrame(data)
        # For simplicity every int column is treated as float
        self.__df = integerToFloat(self.__df)

    def getRawFrame(self) -> pd.DataFrame:
        return self.__df

    @property
    def nRows(self) -> int:
        return self.__df.shape[0]

    @property
    def nColumns(self) -> int:
        return self.__df.shape[1]

    @staticmethod
    def fromShape(s: Shape) -> 'Frame':
        """ Produces a 'dummy' dataframe with a specified shape and 5 rows """
        columns = s.colNames
        types = s.colTypes
        index = s.index
        indexTypes = s.indexTypes

        def getDataForType(dt: Type):
            if dt == Types.Ordinal:
                col = _ordinal
            elif dt == Types.Nominal:
                col = _nominal
            elif dt == Types.Numeric:
                col = _numeric
            elif dt == Types.String:
                col = _string
            elif dt == Types.Datetime:
                col = _date
            else:
                raise ValueError()
            return col

        data = dict()
        for n, t in zip(columns, types):
            data[n] = getDataForType(t)
        df = pd.DataFrame(data)
        pi: pd.Index
        if len(index) == 1:
            pi = pd.Index(getDataForType(indexTypes[0].type), name=index[0])
        else:
            values = [getDataForType(dt.type) for dt in indexTypes]
            pi = pd.MultiIndex.from_arrays(values, names=index)
        df = df.set_index(pi)
        return Frame(df)

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
    def indexValues(self) -> List:
        """ Return the row indices as a list of values """
        return self.__df.index.tolist()

    def setIndex(self, col: Union[List[str], str]) -> 'Frame':
        """
        Sets index of the dataframe

        :param col: the column number or name
        :return: a new frame with the new index
        """
        d = self.__df.set_index(col, drop=True, inplace=False)
        return Frame(d)

    def head(self, n: int = 10) -> pd.DataFrame:
        return self.__df.head(n)

    def to_dict(self, _list: bool = True) -> Dict[str, List]:
        return self.__df.to_dict(orient='list' if _list else 'dict')

    @property
    def shape(self) -> Shape:
        """ The shape of a Frame

        :return: Shape object
        """
        s = Shape()

        # Types are set in a more readable format using type_dict to convert names
        s.colNames = list()
        s.colTypes = list()
        # Index of the columns which are set as indexes
        s.index = list()
        s.indexTypes = list()

        # Index columns
        for i in range(self.__df.index.nlevels):
            index: pd.Index = self.__df.index.get_level_values(i)
            s.index.append(index.name if index.name else 'Unnamed')
            s.indexTypes.append(IndexType(wrapperType(index.dtype)))

        # Columns
        for col, type_val in self.__df.dtypes.items():
            wrappedType = wrapperType(type_val)
            s.colNames.append(col)
            s.colTypes.append(wrappedType)
        return s
