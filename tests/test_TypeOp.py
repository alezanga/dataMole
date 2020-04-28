import copy

import pandas as pd

from data_preprocessor.data import Frame
from data_preprocessor.data.types import Types
from data_preprocessor.operation.all import TypeOp


def test_rename():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = TypeOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions({0: Types.String, 3: Types.Datetime, 2: Types.Categorical})

    os = copy.deepcopy(f.shape)
    os.col_types = [Types.String, Types.Numeric, Types.Categorical, Types.Datetime]

    assert op.getOutputShape() == os

    g = op.execute(f)
    gd = {'col1': ['1.0', '2.0', '3.0', '4.0', '10.0'], 'col2': [3, 4, 5, 6, 0],
          'col3': ['q', '2', 'c', '4', 'x'],
          'date': list(map(pd.Timestamp, d['date']))}
    assert g.to_dict() == gd


def test_unsetOptions():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = TypeOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(new_types={0: Types.String})

    assert op.getOptions() == ({0: Types.String}, f.shape)

    op.unsetOptions()

    assert op.getOptions() == ({}, f.shape)
