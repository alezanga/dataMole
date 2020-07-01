import pandas as pd
import pytest
from numpy import int64

from data_preprocessor.data import Frame, Shape
from data_preprocessor.data.types import Types, IndexType


#
# def test_integerToFloat():
#     df = pd.read_csv('../../datasets/merged-inner-w23-elsa.csv')
#     b = integerToFloat(df)
#
#     # Check it gets the same result as the slow version
#     integerCols = df.select_dtypes(include=int).columns.to_list()
#     n = df[integerCols].astype(float)
#     df[integerCols] = n
#     assert df.equals(b)


def test_rename():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    g = f.rename({'col2': 'new'})
    assert g.colnames == ['col1', 'new', 'col3'] and f.colnames == ['col1', 'col2', 'col3']


def test_rename_bis():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    g = f.rename(['cola', '21eeds', 'ij_'])
    assert g.colnames == ['cola', '21eeds', 'ij_'] and f.colnames == ['col1', 'col2', 'col3']


def test_rename_excep():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    names = f.colnames
    names.append('1')
    with pytest.raises(ValueError):
        f.rename(names)


# TYPING

def test_typing():
    a = 4
    b = pd.DataFrame()
    d: int64 = 12
    c = Frame()
    assert isinstance(type(a), type) and isinstance(type(b), type) and issubclass(type(c), Frame) and \
           isinstance(type(c), type) and isinstance(type(d), type)


# SHAPE

def test_shape():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    s = Shape()
    s.index = ['Unnamed']
    s.indexTypes = [IndexType(Types.Numeric)]
    s.colNames = ['col1', 'col2', 'col3']
    s.colTypes = [Types.Numeric, Types.Numeric, Types.String]

    assert f.shape == s
    assert f.nRows == 5


def test_shape_index():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = Frame(f.getRawFrame().set_index('col3'))

    # Desired shape obj
    s = Shape()
    s.index = ['col3']
    s.indexTypes = [IndexType(Types.String)]
    s.colNames = ['col1', 'col2']
    s.colTypes = [Types.Numeric, Types.Numeric]

    assert f.shape == s
    assert f.nRows == 5


def test_fromShape():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = Frame(d)
    f = Frame(f.getRawFrame().set_index(['col3', 'cold']))

    g = Frame.fromShape(f.shape)

    s = Shape()
    # fromShape does preserve index
    s.colNames = ['col1', 'col2']
    s.colTypes = [Types.Numeric, Types.Numeric]
    s.index = ['col3', 'cold']
    s.indexTypes = [IndexType(Types.String), IndexType(Types.Datetime)]
    assert g.shape == s == f.shape
