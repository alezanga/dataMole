import numpy as np
import pandas as pd
import pytest

from dataMole import exceptions as exp
from dataMole.data import Frame
from dataMole.data.types import Types
from dataMole.operation.typeconversions import ToNumeric, ToCategorical, ToTimestamp, \
    ToString
from tests.utilities import nan_to_None, roundValues, isDictDeepCopy


def test_cat_toNumeric():
    d = {'col1': pd.Categorical(['3', '0', '5', '6', '0']),
         'col2': [3, 4, 5, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToNumeric()
    op.addInputShape(f.shape, pos=0)
    assert op.getOutputShape() is None
    assert op.getOptions() == {'attributes': {}, 'errors': 'raise'}
    op.setOptions(attributes={0: None}, errors='coerce')
    assert op.getOptions() == {'attributes': {0: None}, 'errors': 'coerce'}

    # Predict output shape
    os = f.shape.clone()
    os.colTypes[0] = Types.Numeric
    assert op.getOutputShape() == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: dict()}, errors='raise')
    assert op.getOutputShape() == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3.0, 0.0, 5.0, 6.0, 0.0],
          'col2': [3, 4, 5, 6, 0],
          'col3': ['123', '2', '0.43', '4', '90']}
    assert g.to_dict() == gd
    assert g.shape == os

    # Coerce is the same

    op.setOptions(attributes={0: dict()}, errors='coerce')
    assert op.getOutputShape() == os

    g = op.execute(f)
    assert g.to_dict() == gd
    assert g.shape == os


def test_str_toNumeric():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5, 6, 0],
         'col3': ['123', '2', '0.43', '4', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToNumeric()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: dict(), 2: dict()}, errors='raise')

    # Predict output shape
    os = f.shape.columnsDict
    os['col1'] = Types.Numeric
    os['col3'] = Types.Numeric
    assert op.getOutputShape().columnsDict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: dict(), 2: dict()}, errors='coerce')
    assert op.getOutputShape().columnsDict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3.0, 0.0, 5.0, 6.00, 0.0],
          'col2': [3., 4., 5., 6., 0.0],
          'col3': [123.0, 2.0, 0.43, 4.0, 90.0]}
    assert roundValues(g.to_dict(), 3) == gd
    assert g.shape.columnsDict == os
    assert g.shape.indexDict == f.shape.indexDict


def test_str_toNumeric_coerce():
    d = {'col1': pd.Categorical(['3', np.nan, 5, 6, 0]),
         'col2': [3, 4, 5, 6, 0],
         'col3': [np.nan, '2', '0.43', '4', np.nan]}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToNumeric()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: dict(), 2: dict()}, errors='coerce')

    # Predict output shape
    os = f.shape.columnsDict
    os['col1'] = Types.Numeric
    os['col3'] = Types.Numeric
    assert op.getOutputShape().columnsDict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: dict(), 2: dict()}, errors='coerce')
    assert op.getOutputShape().columnsDict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3., None, 5., 6., 0.],
          'col2': [3., 4., 5., 6., 0.],
          'col3': [None, 2.0, 0.43, 4.0, None]}
    assert roundValues(nan_to_None(g.to_dict()), 2) == gd
    assert g.shape.columnsDict == os
    assert g.shape.indexDict == f.shape.indexDict


def test_unsetOptions_toNumeric():
    d = {'col1': pd.Categorical([1, 2, 3, 4, 10]), 'col2': [3, 4, 5, 6, 0],
         'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = ToNumeric()
    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == {'attributes': {}, 'errors': 'raise'} and not op.hasOptions()
    op.setOptions(attributes={0: dict()}, errors='raise')
    assert op.getOptions() == {'attributes': {0: None}, 'errors': 'raise'}
    assert op._shapes[0] == f.shape

    op.unsetOptions()
    assert op.getOptions() == {'attributes': {}, 'errors': 'raise'}
    assert op._shapes[0] == f.shape

    op.removeInputShape(0)
    assert op.getOptions() == {'attributes': {}, 'errors': 'raise'}
    assert op._shapes == [None]

    op.setOptions(attributes={1: dict()}, errors='coerce')
    assert op.getOptions() == {'attributes': {1: None}, 'errors': 'coerce'}
    assert op._shapes == [None]

    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == {'attributes': {1: None}, 'errors': 'coerce'}
    assert op._shapes[0] == f.shape


# toCATEGORY

def test_unsetOptions_toCategory():
    d = {'col1': pd.Categorical([1, 2, 3, 4, 10]), 'col2': [3, 4, 5, 6, 0],
         'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = ToCategorical()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': ' " 2 e + " 1 ', 'ordered': True}})
    assert op.getOptions() == {'attributes': {0: {'cat': '"2 e +" 1', 'ordered': True}}}
    assert op._ToCategorical__attributes == {0: (['2 e +', '1'], True)}
    assert op._shapes == [f.shape]

    op.unsetOptions()
    assert op.getOptions() == {'attributes': dict()}
    assert op._ToCategorical__attributes == dict()
    assert op._shapes == [f.shape]

    op.removeInputShape(0)
    assert op.getOptions() == {'attributes': dict()}
    assert op._ToCategorical__attributes == dict()
    assert op._shapes == [None]

    op.setOptions(attributes={1: dict()})
    assert op.getOptions() == {'attributes': {1: {'cat': '', 'ordered': False}}}
    assert op._ToCategorical__attributes == {1: (None, None)}
    assert op._shapes == [None]
    assert op.getOutputShape() is None

    op.addInputShape(f.shape, pos=0)
    assert op.getOptions() == {'attributes': {1: {'cat': '', 'ordered': False}}}
    assert op._ToCategorical__attributes == {1: (None, None)}
    assert op._shapes == [f.shape]


def test_str_toCategory():
    d = {'col1': pd.Categorical(["3", "0", "5", "6", "0"]),
         'col2': ["3", "4", "5.1", "6", None],
         'col3': ['123', '2', '0.43', 'nan', '90']}

    # 'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
    #                   dtype='datetime64[ns]')}
    f = Frame(d)

    op = ToCategorical()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={1: {'cat': '4 3 0', 'ordered': True}, 2: dict()})

    # Predict output shape
    os = f.shape.columnsDict
    os['col3'] = Types.Nominal
    os['col2'] = Types.Ordinal
    assert op.getOutputShape().columnsDict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={1: {'cat': '4 3 0', 'ordered': True}, 2: dict()})
    assert op.getOutputShape().columnsDict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': ["3", "0", "5", "6", "0"],
          'col2': ['3', '4', None, None, None],
          'col3': ['123', '2', '0.43', 'nan', '90']}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.columnsDict == os


def test_num_toCategory():
    d = {'col1': pd.Categorical([3, 0, 5, 6, 0]),
         'col2': [3, 4, 5.1, 6, 0],
         'col4': [1, 2, 3, 4, 5],  # this will become a float
         'col3': ['123', '2', '0.43', '4', '90']}

    f = Frame(d)

    op = ToCategorical()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={1: dict(), 2: dict()})

    # Predict output shape
    os = f.shape.columnsDict
    os['col2'] = Types.Nominal
    os['col4'] = Types.Nominal
    assert op.getOutputShape().columnsDict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={1: dict(), 2: dict()})
    assert op.getOutputShape().columnsDict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': [3, 0, 5, 6, 0],
          'col2': ["3.0", "4.0", "5.1", "6.0", "0.0"],
          'col3': ['123', '2', '0.43', '4', '90'],
          'col4': ["1.0", "2.0", "3.0", "4.0", "5.0"]}
    assert g.to_dict() == gd
    assert g.shape.columnsDict == os


def test_cat_toCategory():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0"]),
         'col2': [3, 4, 5.1, 6, 0],
         'col4': [1, 2, 3, 4, 5],  # this will become a float
         'col3': ['123', '2', '0.43', '4', '90']}

    f = Frame(d)

    op = ToCategorical()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': '5 0'}})

    # Predict output shape
    os = f.shape.columnsDict
    assert op.getOutputShape().columnsDict == os

    # Removing options/input_shape causes None to be returned
    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, pos=0)
    op.unsetOptions()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: {'cat': '5 0'}})
    assert op.getOutputShape().columnsDict == os  # Re-adding everything

    g = op.execute(f)
    gd = {'col1': ["5", "0", "5", None, "0"],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0],
          'col3': ['123', '2', '0.43', '4', '90'],
          'col4': [1.0, 2.0, 3.0, 4.0, 5.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.columnsDict == os


def test_ordinal_to_ordinal_cat():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0"], ordered=True),
         'col2': [3, 4, 5.1, 6, 0]}

    f = Frame(d)

    op = ToCategorical()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': '5 0 1', 'ordered': True}})

    # Predict output shape
    os = f.shape.columnsDict
    assert op.getOutputShape().columnsDict == os

    g = op.execute(f)
    gd = {'col1': ["5", "0", "5", None, "0"],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.columnsDict == os
    assert list(g.getRawFrame()['col1'].dtype.categories) == ['5', '0', '1']
    assert g.getRawFrame()['col1'].dtype.ordered


def test_ordinal_to_nominal_cat():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0"], ordered=True),
         'col2': [3, 4, 5.1, 6, 0]}

    f = Frame(d)

    op = ToCategorical()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': '5 0 1 2', 'ordered': False}})

    # Predict output shape
    os = f.shape.columnsDict
    os['col1'] = Types.Nominal
    assert op.getOutputShape().columnsDict == os

    g = op.execute(f)
    gd = {'col1': ["5", "0", "5", None, "0"],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.columnsDict == os
    assert list(g.getRawFrame()['col1'].dtype.categories) == ['5', '0', '1', '2']
    assert g.getRawFrame()['col1'].dtype.ordered is False

    op.setOptions(attributes={0: {'cat': '5 0 1 2'}})
    e = op.execute(f)
    assert nan_to_None(g.to_dict()) == nan_to_None(e.to_dict())


def test_nominal_to_nominal_cat():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0 ww"], ordered=False),
         'col2': [3, 4, 5.1, 6, 0]}

    f = Frame(d)

    op = ToCategorical()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': 'U 0 1 2', 'ordered': False}})

    # Predict output shape
    os = f.shape.columnsDict
    os['col1'] = Types.Nominal
    assert op.getOutputShape().columnsDict == os

    g = op.execute(f)
    gd = {'col1': [None, "0", None, 'U', None],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.columnsDict == os
    assert list(g.getRawFrame()['col1'].dtype.categories) == ['U', '0', '1', '2']
    assert g.getRawFrame()['col1'].dtype.ordered is False


def test_nominal_to_ordinal_cat():
    d = {'col1': pd.Categorical(["5", "0", "5", "U", "0 ww"], ordered=False),
         'col2': [3, 4, 5.1, 6, 0]}

    f = Frame(d)

    op = ToCategorical()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(attributes={0: {'cat': 'U 0 1 5', 'ordered': True}})

    # Predict output shape
    os = f.shape.columnsDict
    os['col1'] = Types.Ordinal
    assert op.getOutputShape().columnsDict == os

    g = op.execute(f)
    gd = {'col1': ['5', '0', '5', 'U', None],
          'col2': [3.0, 4.0, 5.1, 6.0, 0.0]}
    assert nan_to_None(g.to_dict()) == gd
    assert g.shape.columnsDict == os
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
    sd = f.shape.clone()
    sd.colTypes[3] = Types.Datetime
    assert op.getOutputShape() == sd

    g = op.execute(f)
    dateCol = g.getRawFrame()['cold']
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

    assert op.getOptions() == {
        'attributes': {},
        'errors': 'raise'
    }

    op.setOptions(attributes={0: dict(), 2: {'format': '%Y %B'}, 3: {'format': '%d%m%Y'}},
                  errors='raise')
    assert op.getOutputShape().colTypes == [Types.Datetime, Types.Numeric, Types.Datetime,
                                            Types.Datetime]

    assert op.getOptions() == {
        'attributes': {0: {'format': ''}, 2: {'format': '%Y %B'}, 3: {'format': '%d%m%Y'}},
        'errors': 'raise'
    }

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

    with pytest.raises(exp.OptionValidationError):
        op.setOptions(attributes={}, errors='raise')
    assert not op.hasOptions() and op.getOutputShape() is None

    with pytest.raises(exp.OptionValidationError):
        op.setOptions(attributes={0: {'format': '%s'}}, errors='')
    assert not op.hasOptions() and op.getOutputShape() is None

    op.setOptions(attributes={0: {'format': '%d'}}, errors='coerce')
    assert op.hasOptions()
    assert op.getOutputShape().colTypes == [Types.Datetime, Types.Numeric, Types.String,
                                            Types.String]


def test_toString():
    d = {'col1': ['3', '0', '5', '6', '0'],
         'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': ['05091988', '22121994', '21111995', '22061994', '12122012']
         }

    f = Frame(d)

    op = ToString()
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None

    opts = {
        'attributes': {1: None}
    }
    assert op.getOptions() == {'attributes': dict()}

    op.setOptions(**opts)
    assert op.getOutputShape().colTypes == [Types.String, Types.String, Types.String, Types.String]

    assert op.getOptions() == opts
    assert isDictDeepCopy(op.getOptions(), opts)

    g = op.execute(f)
    assert op.getOutputShape() == g.shape
