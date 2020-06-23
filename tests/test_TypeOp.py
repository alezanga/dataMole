import copy

import pandas as pd
import pytest

from data_preprocessor.data import Frame
from data_preprocessor.data.types import Types
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.type import ToNumericOp, ToCategoricalOp, ToTimestamp
from tests.utilities import nan_to_None


def test_cat_toNumeric():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToNumericOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: dict()})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    os['col1'] = Types.Numeric
    assert op.getOutputShape().col_type_dict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: dict()})
    assert op.getOutputShape().col_type_dict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3.0, 0.0, 5.0, 6.0, 0.0],
          'col2': [3, 4, 5, 6, 0],
          'col3': ['123', '2', '0.43', '4', '90']}
    assert g.to_dict() == gd
    assert g.shape.col_type_dict == os


def test_str_toNumeric():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToNumericOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: dict(), 2: dict()})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    os['col1'] = Types.Numeric
    os['col3'] = Types.Numeric
    assert op.getOutputShape().col_type_dict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: dict(), 2: dict()})
    assert op.getOutputShape().col_type_dict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3, 0, 5, 6, 0],
          'col2': [3, 4, 5, 6, 0],
          'col3': [123.0, 2.0, 0.43, 4.0, 90.0]}
    assert g.to_dict() == gd
    assert g.shape.col_type_dict == os


def test_unsetOptions_toNumeric():
    d = {'col1': pd.Categorical([1, 2, 3, 4, 10]), 'col2': [3, 4, 5, 6, 0],
         'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = ToNumericOp()
    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == {'attributes': {}} and not op.hasOptions()
    op.setOptions(attributes={0: dict()})
    assert op.getOptions() == {'attributes': {0: None}}
    assert op._shapes[0] == f.shape

    op.unsetOptions()
    assert op.getOptions() == {'attributes': {}}
    assert op._shapes[0] == f.shape

    op.removeInputShape(0)
    assert op.getOptions() == {'attributes': {}}
    assert op._shapes == [None]

    op.setOptions(attributes={1: dict()})
    assert op.getOptions() == {'attributes': {1: None}}
    assert op._shapes == [None]

    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == {'attributes': {1: None}}
    assert op._shapes[0] == f.shape


# toCATEGORY

def test_unsetOptions_toCategory():
    d = {'col1': pd.Categorical([1, 2, 3, 4, 10]), 'col2': [3, 4, 5, 6, 0],
         'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': ' " 2 e + " 1 ', 'ordered': True}})
    assert op.getOptions() == {'attributes': {0: {'cat': '"2 e +" 1', 'ordered': True}}}
    assert op._ToCategoricalOp__attributes == {0: (['2 e +', '1'], True)}
    assert op._shapes == [f.shape]

    op.unsetOptions()
    assert op.getOptions() == {'attributes': dict()}
    assert op._ToCategoricalOp__attributes == dict()
    assert op._shapes == [f.shape]

    op.removeInputShape(0)
    assert op.getOptions() == {'attributes': dict()}
    assert op._ToCategoricalOp__attributes == dict()
    assert op._shapes == [None]

    op.setOptions(attributes={1: dict()})
    assert op.getOptions() == {'attributes': {1: {'cat': '', 'ordered': False}}}
    assert op._ToCategoricalOp__attributes == {1: (None, None)}
    assert op._shapes == [None]
    assert op.getOutputShape() is None

    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == {'attributes': {1: {'cat': '', 'ordered': False}}}
    assert op._ToCategoricalOp__attributes == {1: (None, None)}
    assert op._shapes == [f.shape]


def test_str_toCategory():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', 'nan', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={1: {'cat': '3.0 4.0 0.0', 'ordered': True}, 2: dict()})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    os['col3'] = Types.Nominal
    os['col2'] = Types.Ordinal
    assert op.getOutputShape().col_type_dict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={1: {'cat': '3.0 4.0 0.0', 'ordered': True}, 2: dict()})
    assert op.getOutputShape().col_type_dict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3, 0, 5, 6, 0],
          'col2': ['3.0', '4.0', None, None, '0.0'],
          'col3': ['123', '2', '0.43', 'nan', '90']}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.col_type_dict == os


def test_num_toCategory():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5.1, 6, 0],
         'col4': [1, 2, 3, 4, 5],  # this will become a float
         'col3': ['123', '2', '0.43', '4', '90']}

    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={1: dict(), 2: dict()})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    os['col2'] = Types.Nominal
    os['col4'] = Types.Nominal
    assert op.getOutputShape().col_type_dict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={1: dict(), 2: dict()})
    assert op.getOutputShape().col_type_dict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3, 0, 5, 6, 0],
          'col2': ["3.0", "4.0", "5.1", "6.0", "0.0"],
          'col3': ['123', '2', '0.43', '4', '90'],
          'col4': ["1.0", "2.0", "3.0", "4.0", "5.0"]}
    assert g.to_dict() == gd
    assert g.shape.col_type_dict == os


def test_cat_toCategory():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0"]),
         'col2': [3, 4, 5.1, 6, 0],
         'col4': [1, 2, 3, 4, 5],  # this will become a float
         'col3': ['123', '2', '0.43', '4', '90']}

    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': '5 0'}})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    assert op.getOutputShape().col_type_dict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: {'cat': '5 0'}})
    assert op.getOutputShape().col_type_dict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': ["5", "0", "5", None, "0"],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0],
          'col3': ['123', '2', '0.43', '4', '90'],
          'col4': [1.0, 2.0, 3.0, 4.0, 5.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.col_type_dict == os


def test_ordinal_to_ordinal_cat():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0"], ordered=True),
         'col2': [3, 4, 5.1, 6, 0]}

    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': '5 0 1', 'ordered': True}})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    assert op.getOutputShape().col_type_dict == os

    g = op.execute(f)
    gd = {'col1': ["5", "0", "5", None, "0"],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.col_type_dict == os
    assert list(g.getRawFrame()['col1'].dtype.categories) == ['5', '0', '1']
    assert g.getRawFrame()['col1'].dtype.ordered


def test_ordinal_to_nominal_cat():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0"], ordered=True),
         'col2': [3, 4, 5.1, 6, 0]}

    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': '5 0 1 2', 'ordered': False}})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    os['col1'] = Types.Nominal
    assert op.getOutputShape().col_type_dict == os

    g = op.execute(f)
    gd = {'col1': ["5", "0", "5", None, "0"],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.col_type_dict == os
    assert list(g.getRawFrame()['col1'].dtype.categories) == ['5', '0', '1', '2']
    assert g.getRawFrame()['col1'].dtype.ordered is False

    op.setOptions(attributes={0: {'cat': '5 0 1 2'}})
    e = op.execute(f)
    assert nan_to_None(g.to_dict()) == nan_to_None(e.to_dict())


def test_nominal_to_nominal_cat():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0 ww"], ordered=False),
         'col2': [3, 4, 5.1, 6, 0]}

    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': 'U 0 1 2', 'ordered': False}})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    os['col1'] = Types.Nominal
    assert op.getOutputShape().col_type_dict == os

    g = op.execute(f)
    gd = {'col1': [None, "0", None, 'U', None],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.col_type_dict == os
    assert list(g.getRawFrame()['col1'].dtype.categories) == ['U', '0', '1', '2']
    assert g.getRawFrame()['col1'].dtype.ordered is False


def test_nominal_to_ordinal_cat():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0 ww"], ordered=False),
         'col2': [3, 4, 5.1, 6, 0]}

    f = Frame(d)

    op = ToCategoricalOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': 'U 0 1 5', 'ordered': True}})

    # Predict output shape
    os = copy.deepcopy(f.shape).col_type_dict
    os['col1'] = Types.Ordinal
    assert op.getOutputShape().col_type_dict == os

    g = op.execute(f)
    gd = {'col1': ['5', '0', '5', 'U', None],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.col_type_dict == os
    assert list(g.getRawFrame()['col1'].dtype.categories) == ['U', '0', '1', '5']
    assert g.getRawFrame()['col1'].dtype.ordered is True


def test_str_to_Timestamp_raise():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90'],
         'cold': ['05091988', '22121994', '21111995', '22061994', '12122012']
         }

    f = Frame(d)

    op = ToTimestamp()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.setOptions(attributes={3: {'format': '%d%m%Y'}}, errors='raise')
    sd = f.shape.copy(True)
    sd.col_types[3] = Types.Datetime
    assert op.getOutputShape() == sd

    g = op.execute(f)
    dateCol = g.columnsAt('cold').getRawFrame()
    assert op.getOutputShape() == g.shape == sd


def test_str_to_Timestamp_coerce():
    d = {'col1': ['3', '0', '5', '6', '0'],
         'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': ['05091988', '22121994', '21111995', '22061994', '12122012']
         }

    f = Frame(d)

    op = ToTimestamp()
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: dict(), 2: {'format': '%Y %B'}, 3: {'format': '%d%m%Y'}},
                  errors='raise')
    assert op.getOutputShape().col_types == [Types.Datetime, Types.Numeric, Types.Datetime,
                                             Types.Datetime]

    # Raise exception since pandas cannot convert all values to datetime
    with pytest.raises(Exception):
        op.execute(f)

    op.setOptions(attributes={0: dict(), 2: {'format': '%Y %B'}, 3: {'format': '%d%m%Y'}},
                  errors='coerce')
    g = op.execute(f)
    pg = g.getRawFrame()
    assert op.getOutputShape() == g.shape


def test_str_to_Timestamp_validation():
    d = {'col1': ['3', '0', '5', '6', '0'],
         'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': ['05091988', '22121994', '21111995', '22061994', '12122012']
         }

    f = Frame(d)

    op = ToTimestamp()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None

    with pytest.raises(OptionValidationError):
        op.setOptions(attributes={}, errors='raise')
    assert not op.hasOptions() and op.getOutputShape() is None

    with pytest.raises(OptionValidationError):
        op.setOptions(attributes={0: {'format': '%s'}}, errors='')
    assert not op.hasOptions() and op.getOutputShape() is None

    op.setOptions(attributes={0: {'format': '%d'}}, errors='coerce')
    assert op.hasOptions()
    assert op.getOutputShape().col_types == [Types.Datetime, Types.Numeric, Types.String,
                                             Types.String]
