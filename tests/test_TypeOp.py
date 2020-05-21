import copy

import pandas as pd

from data_preprocessor.data import Frame
from data_preprocessor.data.types import Types
from data_preprocessor.operation.type import ToNumericOp, ToCategoricalOp


def test_cat_toNumeric():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToNumericOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attribute_indexes=0)

    # Predict output shape
    os = copy.deepcopy(f.shape)
    os.col_types = [Types.Numeric, Types.Numeric, Types.String]
    assert op.getOutputShape() == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attribute_indexes=0)
    assert op.getOutputShape() == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3.0, 0.0, 5.0, 6.0, 0.0],
          'col2': [3, 4, 5, 6, 0],
          'col3': ['123', '2', '0.43', '4', '90']}
    assert g.to_dict() == gd
    assert g.shape == os


def test_str_toNumeric():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToNumericOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attribute_indexes=2)

    # Predict output shape
    os = copy.deepcopy(f.shape)
    os.col_types = [Types.Categorical, Types.Numeric, Types.Numeric]
    assert op.getOutputShape() == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attribute_indexes=2)
    assert op.getOutputShape() == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3, 0, 5, 6, 0],
          'col2': [3, 4, 5, 6, 0],
          'col3': [123.0, 2.0, 0.43, 4.0, 90.0]}
    assert g.to_dict() == gd
    assert g.shape == os


def test_unsetOptions_toNumeric():
    d = {'col1': pd.Categorical([1, 2, 3, 4, 10]), 'col2': [3, 4, 5, 6, 0],
         'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = ToNumericOp()
    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == [None] and not op.hasOptions()
    op.setOptions(attribute_indexes=0)
    assert op.getOptions() == [0]
    assert op._shape[0] == f.shape

    op.unsetOptions()
    assert op.getOptions() == [None]
    assert op._shape[0] == f.shape

    op.removeInputShape(0)
    assert op.getOptions() == [None]
    assert op._shape == [None]

    op.setOptions(attribute_indexes=1)
    assert op.getOptions() == [1]
    assert op._shape == [None]

    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == [1]
    assert op._shape[0] == f.shape


# toCATEGORY

def test_unsetOptions_toCategory():
    d = {'col1': pd.Categorical([1, 2, 3, 4, 10]), 'col2': [3, 4, 5, 6, 0],
         'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attribute_indexes=0)
    assert op.getOptions() == [0]
    assert op._shape == [f.shape]

    op.unsetOptions()
    assert op.getOptions() == [None]
    assert op._shape == [f.shape]

    op.removeInputShape(0)
    assert op.getOptions() == [None]
    assert op._shape == [None]

    op.setOptions(attribute_indexes=1)
    assert op.getOptions() == [1]
    assert op._shape == [None]

    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == [1]
    assert op._shape == [f.shape]


def test_str_toCategory():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attribute_indexes=2)

    # Predict output shape
    os = copy.deepcopy(f.shape)
    os.col_types = [Types.Categorical, Types.Numeric, Types.Categorical]
    assert op.getOutputShape() == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attribute_indexes=2)
    assert op.getOutputShape() == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3, 0, 5, 6, 0],
          'col2': [3, 4, 5.1, 6, 0],
          'col3': ['123', '2', '0.43', '4', '90']}
    assert g.to_dict() == gd
    assert g.shape == os


def test_num_toCategory():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attribute_indexes=1)

    # Predict output shape
    os = copy.deepcopy(f.shape)
    os.col_types = [Types.Categorical, Types.Categorical, Types.String]
    assert op.getOutputShape() == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attribute_indexes=1)
    assert op.getOutputShape() == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3, 0, 5, 6, 0],
          'col2': [3, 4, 5.1, 6, 0],
          'col3': ['123', '2', '0.43', '4', '90']}
    assert g.to_dict() == gd
    assert g.shape == os


def test_date_toCategory():
    # Date is not an accepted type so it must do nothing
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90'],
         'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')
         }

    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attribute_indexes=3)

    # Predict output shape which should not change
    os = copy.deepcopy(f.shape)
    os.col_types = [Types.Categorical, Types.Numeric, Types.String, Types.Datetime]
    assert op.getOutputShape() == os

    g = op.execute(f)  # changes nothing
    gd = {'col1': [3, 0, 5, 6, 0],
          'col2': [3, 4, 5.1, 6, 0],
          'col3': ['123', '2', '0.43', '4', '90'],
          'cold': list(map(pd.Timestamp, d['cold'].tolist()))}
    assert g.to_dict() == gd
    assert g.shape == os
