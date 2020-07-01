import pandas as pd

from data_preprocessor import data
from data_preprocessor.data.types import Types, IndexType
from data_preprocessor.operation.JoinOp import JoinOp, JoinType as jt


def test_join_on_index():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    e = {'col2': pd.Categorical([3, 4, 5, 6, 0]), 'cowq': [1, 2, 3, 4.0, 10],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = data.Frame(d)
    g = data.Frame(e)

    f = f.setIndex('col1')
    g = g.setIndex('col2')

    op = JoinOp()
    op.setOptions('_l', '_r', True, None, None, jt.Inner)

    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 1)
    s = {
        'cowq': Types.Numeric,
        'col2': Types.Numeric,
        'col3_l': Types.String,
        'col3_r': Types.String,
        'date_l': Types.String,
        'date_r': Types.Datetime
    }
    di = {
        'Unnamed': IndexType(Types.String)
    }
    assert op.getOutputShape().columnsDict == s
    assert op.getOutputShape().indexDict == di

    h = op.execute(f, g)

    assert h.shape.columnsDict == s


def test_join_on_cols():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical([3, 4, 5, 7, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = data.Frame(d)
    g = data.Frame(e)

    f = f.setIndex('col1')
    g = g.setIndex('col2')

    op = JoinOp()
    op.setOptions('_l', '_r', False, 2, 1, jt.Right)

    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 1)
    s = {
        'cowq': Types.Numeric,
        'col2': Types.Numeric,
        'col3_l': Types.String,
        'col3_r': Types.String,
        'date_l': Types.String,
        'date_r': Types.Datetime
    }
    assert op.getOutputShape().columnsDict == s

    h = op.execute(f, g)

    assert h.shape.columnsDict == s
    assert h.shape.indexDict == {'Unnamed': IndexType(Types.Numeric)}
    # Note that merge does not preserve index


def test_join_on_date():
    # TOFIX: or delete this possibility
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1934', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical([3, 4, 5, 6, 0], ordered=True),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date1': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                            dtype='datetime64[ns]')}
    f = data.Frame(d)
    g = data.Frame(e)

    f = f.setIndex('col1')
    g = g.setIndex('col2')

    op = JoinOp()
    op.setOptions('_l', '_r', False, 3, 2, jt.Outer)

    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 1)
    s = {
        'cowq': Types.Numeric,
        'col1': Types.Numeric,
        'col2_l': Types.Numeric,
        'col2_r': Types.Ordinal,
        'col3_l': Types.String,
        'col3_r': Types.String,
        'date': Types.Datetime,
        'date1': Types.Datetime
    }
    assert op.getOutputShape().columnsDict == s
    assert op.getOutputShape().index is None

    h = op.execute(f, g)

    assert h.shape.columnsDict == s
    assert h.shape.index == {'Unnamed': IndexType(Types.Numeric)}
