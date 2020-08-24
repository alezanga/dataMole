import pandas as pd
import pytest

from data_preprocessor import data, exceptions as exc
from data_preprocessor.data.types import Types, IndexType
from data_preprocessor.operation.join import Join

jt = Join.JoinType


def test_join_on_index():
    d = {'col1': ['1', '2', '3', '4', '10'], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    e = {'col2': pd.Categorical(['3', '4', '5', '6', '0'], ordered=True),
         'cowq': [1, 2, 3, 4.0, 10],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = data.Frame(d)
    g = data.Frame(e)

    f = f.setIndex('col1')
    g = g.setIndex('col2')

    defaultOpts = '_l', '_r', True, None, None, jt.Left
    op = Join()
    assert op.getOptions() == defaultOpts

    assert op.getOutputShape() is None
    # with pytest.raises(exc.OptionValidationError) as e:
    #     op.setOptions('_ll', '_rr', True, None, None, jt.Inner)
    # CAN set options before shapes
    # assert 'shape' in [a[0] for a in e.value.invalid]
    # assert op.getOptions() == defaultOpts

    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 1)

    # Now set options
    op.setOptions('_ll', '_rr', True, None, None, jt.Inner)
    assert op.getOptions() == (
        '_ll', '_rr', True, None, None, jt.Inner
    )

    dc = {
        'cowq': Types.Numeric,
        'col2': Types.Numeric,
        'col3_ll': Types.String,
        'col3_rr': Types.String,
        'date_ll': Types.String,
        'date_rr': Types.Datetime
    }
    # Note that join does not preserve index name
    di = {
        'Unnamed': IndexType(Types.String)
    }
    s = data.Shape.fromDict(dc, di)
    assert op.getOutputShape() == s

    h = op.execute(f, g)

    assert h.shape == s


def test_join_on_multiindex():
    d = {'col1': ['1', '2', '3', '4', '10'], 'col2': ['3', '4', '5', '6', '0'],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    e = {'col2': pd.Categorical(['3', '4', '5', '6', '0'], ordered=True),
         'cowq': [1, 2, 3, 4.0, 10],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = data.Frame(d)
    g = data.Frame(e)

    f = f.setIndex(['col1', 'col2'])  # String, String
    g = g.setIndex(['col2', 'cowq'])  # Category, Numeric

    defaultOpts = '_l', '_r', True, None, None, jt.Left
    op = Join()
    assert op.getOptions() == defaultOpts

    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 1)

    # Now set options
    op.setOptions('_ll', '_rr', True, None, None, jt.Outer)
    assert op.getOptions() == (
        '_ll', '_rr', True, None, None, jt.Outer
    )

    dc = {
        'col3_ll': Types.String,
        'col3_rr': Types.String,
        'date_ll': Types.String,
        'date_rr': Types.Datetime
    }
    # Join on multiindex is different
    di = {
        'col1': IndexType(Types.String),
        'col2': IndexType(Types.String),
        'cowq': IndexType(Types.Numeric)
    }
    s = data.Shape.fromDict(dc, di)
    assert op.getOutputShape() == s

    h = op.execute(f, g)

    assert h.shape == s


def test_join_on_multiindex_exc():
    d = {'col1': ['1', '2', '3', '4', '10'], 'col2': [3, 4, 5, 6, 0],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    e = {'col2': pd.Categorical(['3', '4', '5', '6', '0'], ordered=True),
         'cowq': [1, 2, 3, 4.0, 10],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = data.Frame(d)
    g = data.Frame(e)

    f = f.setIndex(['col1', 'col2'])  # String, Numeric
    g = g.setIndex(['col2', 'cowq'])  # Category, Numeric

    op = Join()

    op.addInputShape(f.shape, 0)
    op.addInputShape(g.shape, 1)

    # Now set options
    with pytest.raises(exc.OptionValidationError) as e:
        op.setOptions('_ll', '_rr', True, None, None, jt.Left)
    assert 'type' in [a[0] for a in e.value.invalid]


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

    op = Join()

    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 1)

    op.setOptions('_l', '_r', False, 2, 1, jt.Right)
    assert op.getOptions() == ('_l', '_r', False, 2, 1, jt.Right)
    dc = {
        'cowq': Types.Numeric,
        'col2': Types.Numeric,
        'col3_l': Types.String,
        'col3_r': Types.String,
        'date_l': Types.String,
        'date_r': Types.Datetime
    }
    # Note that merge does not preserve index
    di = {
        'Unnamed': IndexType(Types.Numeric)  # Default index
    }

    s = data.Shape.fromDict(dc, di)
    assert op.getOutputShape() == s
    h = op.execute(f, g)
    assert h.shape == s

# def test_join_on_date():
#     # TOFIX: or delete this possibility
#     d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
#          'date': pd.Series(['05-09-1934', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
#                            dtype='datetime64[ns]')}
#     e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical([3, 4, 5, 6, 0], ordered=True),
#          'col3': ['q', '2', 'c', '4', 'x'],
#          'date1': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
#                             dtype='datetime64[ns]')}
#     f = data.Frame(d)
#     g = data.Frame(e)
#
#     f = f.setIndex('col1')
#     g = g.setIndex('col2')
#
#     op = Join()
#     op.setOptions('_l', '_r', False, 3, 2, jt.Outer)
#
#     op.addInputShape(f.shape, 0)
#     assert op.getOutputShape() is None
#     op.addInputShape(g.shape, 1)
#     s = {
#         'cowq': Types.Numeric,
#         'col1': Types.Numeric,
#         'col2_l': Types.Numeric,
#         'col2_r': Types.Ordinal,
#         'col3_l': Types.String,
#         'col3_r': Types.String,
#         'date': Types.Datetime,
#         'date1': Types.Datetime
#     }
#     assert op.getOutputShape().columnsDict == s
#     assert op.getOutputShape().index is None
#
#     h = op.execute(f, g)
#
#     assert h.shape.columnsDict == s
#     assert h.shape.index == {'Unnamed': IndexType(Types.Numeric)}
