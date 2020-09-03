import numpy as np
import pandas as pd
import pytest

from dataMole import data
from dataMole.data import Shape
from dataMole.data.types import Types, IndexType
from dataMole.exceptions import OptionValidationError
from dataMole.operation.fill import FillNan
from tests.utilities import nan_to_None, roundValues, isDictDeepCopy


def mapDate(df: dict) -> dict:
    new = dict()
    for k, v in df.items():
        new[k] = list()
        for e in v:
            val = e
            if isinstance(e, pd.Timestamp):
                val = e.strftime(format='%Y-%m-%d')
            new[k].append(val)
    return new


def test_fillnan_mean():
    e = {'col1': [np.nan, 2, np.nan, 4, 10],
         'col2': pd.Categorical(['3', '4', '5', '6', '0'], ordered=True),
         'col3': ['q', '2', 'c', np.nan, np.nan],
         'date': pd.Series(['05-09-1988', '22-12-1994', np.nan, '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    g = g.setIndex('col2')

    op = FillNan()
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 0)
    op.setOptions(selected={0: None, 2: None}, fillMode='mean')
    opts = op.getOptions()
    expOpts = {
        'selected': {0: None, 2: None},
        'fillMode': 'mean'
    }
    assert opts == expOpts
    assert isDictDeepCopy(opts, expOpts)

    s = Shape()
    s.colNames = ['col3', 'col1', 'date']
    s.colTypes = [Types.String, Types.Numeric, Types.Datetime]
    s.index = ['col2']
    s.indexTypes = [IndexType(Types.Ordinal)]
    assert op.getOutputShape() == s

    h = op.execute(g)
    assert h.shape == s

    assert mapDate(roundValues(nan_to_None(h.to_dict()), decimals=3)) == {
        'col3': ['q', '2', 'c', None, None],
        'col1': [5.333, 2.0, 5.333, 4.0, 10.0],
        'date': [t.strftime(format='%Y-%m-%d') if not pd.isna(t) else '1997-09-08'
                 for t in e['date']]
    }


def test_fillnan_bfill():
    e = {'col1': [np.nan, 2, np.nan, 4, 10],
         'col2': pd.Categorical(['3', '4', np.nan, np.nan, '0'], ordered=True),
         'col3': ['q', '2', 'c', np.nan, np.nan],
         'date': pd.Series(['05-09-1988', '22-12-1994', np.nan, '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    g = g.setIndex('col1')

    op = FillNan()
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 0)
    assert op.getOptions() == {
        'selected': dict(),
        'fillMode': 'value'  # special option is set at the beginning
    }
    op.setOptions(selected={0: None, 1: None, 2: None}, fillMode='bfill')
    opts = op.getOptions()
    expOpts = {
        'selected': {0: None, 1: None, 2: None},
        'fillMode': 'bfill'
    }
    assert opts == expOpts
    assert isDictDeepCopy(opts, expOpts)

    s = Shape()
    s.colNames = ['col3', 'col2', 'date']
    s.colTypes = [Types.String, Types.Ordinal, Types.Datetime]
    s.index = ['col1']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s

    h = op.execute(g)
    assert h.shape == s

    assert mapDate(roundValues(nan_to_None(h.to_dict()), decimals=3)) == {
        'col3': ['q', '2', 'c', None, None],
        'col2': ['3', '4', '0', '0', '0'],
        'date': [t.strftime(format='%Y-%m-%d') if not pd.isna(t) else '1994-06-22'
                 for t in e['date']]
    }


def test_fillnan_ffill():
    e = {'col1': [np.nan, 2, np.nan, 4, 10],
         'col2': pd.Categorical(['3', '4', np.nan, np.nan, '0'], ordered=True),
         'col3': ['q', '2', 'c', np.nan, np.nan],
         'date': pd.Series(['05-09-1988', np.nan, np.nan, '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    g = g.setIndex('col1')

    op = FillNan()
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 0)
    op.setOptions(selected={0: None, 1: None, 2: None}, fillMode='ffill')
    assert op.getOptions() == {
        'selected': {0: None, 1: None, 2: None},
        'fillMode': 'ffill'
    }

    s = Shape()
    s.colNames = ['col3', 'col2', 'date']
    s.colTypes = [Types.String, Types.Ordinal, Types.Datetime]
    s.index = ['col1']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s

    h = op.execute(g)
    assert h.shape == s

    assert mapDate(roundValues(nan_to_None(h.to_dict()), decimals=3)) == {
        'col3': ['q', '2', 'c', 'c', 'c'],
        'col2': ['3', '4', '4', '4', '0'],
        'date': [t.strftime(format='%Y-%m-%d') if not pd.isna(t) else '1988-05-09'
                 for t in e['date']]
    }


def test_fillnan_byVal_date_num():
    e = {'col1': [np.nan, 2, np.nan, 4, 10],
         'col2': pd.Categorical(['3', '4', np.nan, np.nan, '0'], ordered=True),
         'col3': ['q', '2', 'c', np.nan, np.nan],
         'date': pd.Series(['05-09-1988', np.nan, np.nan, '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]'),
         'col4': [np.nan, 2, np.nan, 4, 10]}
    g = data.Frame(e)

    g = g.setIndex('col1')

    op = FillNan()
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 0)
    with pytest.raises(OptionValidationError):
        op.setOptions(selected={0: {'fill': 'pol'}, 1: {'fill': '23'},  # wrong
                                2: {'fill': '1966-04-02 00:00:30'},
                                3: {'fill': 'march'}},  # wrong
                      fillMode='value')

    op.setOptions(selected={2: {'fill': '1966-04-02 00:00:30'},
                            3: {'fill': '0.9'}},
                  fillMode='value')

    assert op.getOptions() == {
        'selected': {2: {'fill': '1966-04-02 00:00:30'},
                     3: {'fill': '0.9'}},
        'fillMode': 'value'
    }

    s = Shape()
    s.colNames = ['col3', 'col2', 'date', 'col4']
    s.colTypes = [Types.String, Types.Ordinal, Types.Datetime, Types.Numeric]
    s.index = ['col1']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s

    h = op.execute(g)
    assert h.shape == s

    assert mapDate(roundValues(nan_to_None(h.to_dict()), decimals=3)) == {
        'col3': ['q', '2', 'c', None, None],
        'col2': ['3', '4', None, None, '0'],
        'date': [t.strftime(format='%Y-%m-%d') if not pd.isna(t) else '1966-04-02'
                 for t in e['date']],
        'col4': [0.9, 2.0, 0.9, 4.0, 10.0]
    }
