import pandas as pd

from dataMole import data
from dataMole.data import Shape
from dataMole.data.types import Types, IndexType
from dataMole.operation.index import SetIndex, ResetIndex
from tests.utilities import isDictDeepCopy


def test_set_index_num():
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical([3, 4, 5, 6, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    op = SetIndex()
    assert op.getOptions() == {'selected': dict()}
    ops = {'selected': {0: None}}
    op.setOptions(**ops)

    assert op.getOptions() == ops
    assert isDictDeepCopy(op.getOptions(), ops)

    assert op.getOutputShape() is None

    op.addInputShape(g.shape, 0)
    s = Shape()
    s.colNames = ['col3', 'col2', 'date']
    s.colTypes = [Types.String, Types.Nominal, Types.Datetime]
    s.index = ['cowq']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s

    h = op.execute(g)
    assert h.shape == s

    # Reset index

    op = ResetIndex()
    assert op.getOutputShape() is None
    op.addInputShape(h.shape, 0)
    s = Shape()
    s.colNames = ['cowq', 'col2', 'date', 'col3']
    s.colTypes = [Types.Numeric, Types.Nominal, Types.Datetime, Types.String]
    s.index = ['Unnamed']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s
    j = op.execute(h)
    assert j.shape == s


def test_set_index_cat():
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(['3', 4, 5, 6, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    op = SetIndex()
    op.setOptions(selected={1: None, 2: None})
    assert op.getOptions() == {'selected': {1: None, 2: None}}

    assert op.getOutputShape() is None

    op.addInputShape(g.shape, 0)
    s = Shape()
    s.colNames = ['date', 'cowq']
    s.colTypes = [Types.Datetime, Types.Numeric]
    s.index = ['col3', 'col2']
    s.indexTypes = [IndexType(Types.String), IndexType(Types.Nominal)]
    assert op.getOutputShape() == s

    h = op.execute(g)
    assert h.shape == s

    # Reset index

    op = ResetIndex()
    assert op.getOutputShape() is None
    op.addInputShape(h.shape, 0)
    s = Shape()
    s.colNames = ['cowq', 'col2', 'date', 'col3']
    s.colTypes = [Types.Numeric, Types.Nominal, Types.Datetime, Types.String]
    s.index = ['Unnamed']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s
    j = op.execute(h)
    assert j.shape == s


def test_set_index_date():
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(['3', 4, 5, 6, 0], ordered=True),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    op = SetIndex()
    op.setOptions(selected={3: None})

    assert op.getOutputShape() is None

    op.addInputShape(g.shape, 0)
    s = Shape()
    s.colNames = ['cowq', 'col2', 'col3']
    s.colTypes = [Types.Numeric, Types.Ordinal, Types.String]
    s.index = ['date']
    s.indexTypes = [IndexType(Types.Datetime)]
    os = op.getOutputShape()
    assert os == s

    h = op.execute(g)
    hs = h.shape
    assert hs == s

    # Reset index

    op = ResetIndex()
    assert op.getOutputShape() is None
    op.addInputShape(h.shape, 0)
    s = Shape()
    s.colNames = ['cowq', 'col2', 'date', 'col3']
    s.colTypes = [Types.Numeric, Types.Ordinal, Types.Datetime, Types.String]
    s.index = ['Unnamed']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s
    j = op.execute(h)
    assert j.shape == s


def test_set_index_string():
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(['3', 4, 5, 6, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    op = SetIndex()
    op.setOptions(selected={2: None})

    assert op.getOutputShape() is None

    op.addInputShape(g.shape, 0)
    s = Shape()
    s.colNames = ['cowq', 'col2', 'date']
    s.colTypes = [Types.Numeric, Types.Nominal, Types.Datetime]
    s.index = ['col3']
    s.indexTypes = [IndexType(Types.String)]
    os = op.getOutputShape()
    assert os == s

    h = op.execute(g)
    hs = h.shape
    assert hs == s

    # Reset index

    op = ResetIndex()
    assert op.getOutputShape() is None
    op.addInputShape(h.shape, 0)
    s = Shape()
    s.colNames = ['cowq', 'col2', 'date', 'col3']
    s.colTypes = [Types.Numeric, Types.Nominal, Types.Datetime, Types.String]
    s.index = ['Unnamed']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s
    j = op.execute(h)
    assert j.shape == s
