import numpy as np
import pandas as pd

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.operation.merge_values import MergeValuesOp


def test_merge():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)

    op = MergeValuesOp()
    op.setOptions(attribute='col3', values_to_merge=['q', 'x', 2, 'wq'], value=0.02)

    op.addInputShape(f.shape, 0)
    s = f.shape.copy()
    s.col_types[2] = Types.String
    assert op.getOutputShape() == s

    g = op.execute(f)

    assert g != f and g.shape == s


def test_merge_nan():
    d = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical([3, 4, 5, 6, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = data.Frame(d)
    f = f.setIndex('col3')

    op = MergeValuesOp()
    op.setOptions(attribute='col2', values_to_merge=[3, 0, 'q', 'x', 2, 'wq'], value=np.nan)

    op.addInputShape(f.shape, 0)
    s = f.shape.copy()
    assert f.shape.col_types[1] == Types.Categorical
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert g.shape == f.shape
    assert g.columnsAt('col2').to_dict() == {'col2': [np.nan, 4, 5, 6, np.nan]}


def test_merge_index_val():
    d = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical([3, 4, 5, 6, 0]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = data.Frame(d)
    f = f.setIndex('col2')

    op = MergeValuesOp()
    op.setOptions(attribute='col2', values_to_merge=[3, 0], value=88)

    op.addInputShape(f.shape, 0)
    s = f.shape.copy()
    os = op.getOutputShape()
    assert f.shape.col_types[1] == Types.Categorical == os.col_types[1]
    assert os == s

    g = op.execute(f)
    assert g.shape == f.shape
    assert g.columnsAt('col2').to_dict() == {'col2': [88, 4, 5, 6, 88]}
