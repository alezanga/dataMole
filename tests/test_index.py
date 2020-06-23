import pandas as pd

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.operation.index import SetIndexOp


def test_set_index_num():
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical([3, 4, 5, 6, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    op = SetIndexOp()
    op.setOptions(0)

    assert op.getOutputShape() is None

    op.addInputShape(g.shape, 0)
    s = {
        'cowq': Types.Numeric,
        'col2': Types.Nominal,
        'col3': Types.String,
        'date': Types.Datetime
    }
    os = op.getOutputShape()
    assert os.col_type_dict == s
    assert os.index == 'cowq'

    h = op.execute(g)
    hs = h.shape
    assert hs.col_type_dict == s
    assert hs.index == 'cowq'


def test_set_index_cat():
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(['3', 4, 5, 6, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    op = SetIndexOp()
    op.setOptions(1)

    assert op.getOutputShape() is None

    op.addInputShape(g.shape, 0)
    s = {
        'cowq': Types.Numeric,
        'col2': Types.Nominal,
        'col3': Types.String,
        'date': Types.Datetime
    }
    os = op.getOutputShape()
    assert os.col_type_dict == s
    assert os.index == 'col2'

    h = op.execute(g)
    hs = h.shape
    assert hs.col_type_dict == s
    assert hs.index == 'col2'


def test_set_index_date():
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(['3', 4, 5, 6, 0], ordered=True),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    op = SetIndexOp()
    op.setOptions(3)

    assert op.getOutputShape() is None

    op.addInputShape(g.shape, 0)
    s = {
        'cowq': Types.Numeric,
        'col2': Types.Ordinal,
        'col3': Types.String,
        'date': Types.Datetime
    }
    os = op.getOutputShape()
    assert os.col_type_dict == s
    assert os.index == 'date'

    h = op.execute(g)
    hs = h.shape
    assert hs.col_type_dict == s
    assert hs.index == 'date'


def test_set_index_string():
    e = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(['3', 4, 5, 6, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    op = SetIndexOp()
    op.setOptions(2)

    assert op.getOutputShape() is None

    op.addInputShape(g.shape, 0)
    s = {
        'cowq': Types.Numeric,
        'col2': Types.Nominal,
        'col3': Types.String,
        'date': Types.Datetime
    }
    os = op.getOutputShape()
    assert os.col_type_dict == s
    assert os.index == 'col3'

    h = op.execute(g)
    hs = h.shape
    assert hs.col_type_dict == s
    assert hs.index == 'col3'
