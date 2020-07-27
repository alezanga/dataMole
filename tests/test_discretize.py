from typing import List, Tuple

import numpy as np
import pytest

from data_preprocessor import data
from data_preprocessor import exceptions as exp
from data_preprocessor.data.types import Types
from data_preprocessor.operation.discretize import BinsDiscretizer, BinStrategy, RangeDiscretizer
from tests.utilities import nan_to_None


def test_discretize_num_uniform():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = BinsDiscretizer()
    assert op.getOutputShape() is None
    assert op.getOptions() == {
        'attributes': {},
        'strategy': BinStrategy.Uniform,
        'suffix': (True, '_discretized')
    }

    tabOpts = {0: {'bins': '2'}, 1: {'bins': '3'}}
    stra = BinStrategy.Uniform

    op.setOptions(attributes=tabOpts, strategy=stra, suffix=(False, None))
    # Check for side effects
    tabOpts[0]['bins'] = '23'
    stra = '11'

    assert op.getOptions() == {
        'attributes': {0: {'bins': '2'}, 1: {'bins': '3'}},
        'strategy': BinStrategy.Uniform,
        'suffix': (False, None)
    }

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    s.colTypes[0] = Types.Ordinal
    s.colTypes[1] = Types.Ordinal
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert nan_to_None(g.to_dict()) == {
        'col1': ['0.0', '0.0', '0.0', '1.0', '1.0'],
        'col2': ['0.0', '1.0', None, '2.0', None],
        'ww': [3, 1, 'ww', '1', '1']
    }
    assert g.shape == s


def test_discretize_num_uniform_nondrop():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan],
         'ww': [3, 1, 'ww', '1', '1'], 'col2_discre': [1, 1, 1, 1, 1]}  # col2_discre replaced
    f = data.Frame(d)

    op = BinsDiscretizer()
    assert op.getOutputShape() is None
    assert op.getOptions() == {
        'attributes': {},
        'strategy': BinStrategy.Uniform,
        'suffix': (True, '_discretized')
    }
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform,
                  suffix=(True, '_discre'))

    assert op.getOptions() == {
        'attributes': {0: {'bins': '2'}, 1: {'bins': '3'}},
        'strategy': BinStrategy.Uniform,
        'suffix': (True, '_discre')
    }

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    cd = s.columnsDict
    cd['col1_discre'] = Types.Ordinal
    cd['col2_discre'] = Types.Ordinal
    s = data.Shape.fromDict(cd, s.indexDict)
    assert op.getOutputShape() == s

    g = op.execute(f)
    expected_output = {
        'col1_discre': ['0.0', '0.0', '0.0', '1.0', '1.0'],
        'col2_discre': ['0.0', '1.0', None, '2.0', None],
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, None, 6, None],
        'ww': [3, 1, 'ww', '1', '1']
    }
    assert nan_to_None(g.to_dict()) == expected_output
    assert g.shape == s

    # Check that output is the same as with drop
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform,
                  suffix=(False, None))
    o = op.execute(f)
    assert expected_output['col1_discre'] == nan_to_None(o.to_dict())['col1']
    assert expected_output['col2_discre'] == nan_to_None(o.to_dict())['col2']
    assert expected_output['col1'] != nan_to_None(o.to_dict())['col1']
    assert expected_output['col2'] != nan_to_None(o.to_dict())['col2']


def test_discretize_range():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = RangeDiscretizer()
    assert op.getOutputShape() is None
    assert op.getOptions() == {
        'table': {},
        'suffix': (True, '_bins')
    }
    op.setOptions(table={0: {'bins': [0, 2, 4, 6, 8, 10], 'labels': '"a u with\'" b c d e'},
                         1: {'bins': [0, 2, 4, 7], 'labels': 'A B C'}},
                  suffix=(False, None))
    assert op.getOptions() == {
        'table': {0: {'bins': [0, 2, 4, 6, 8, 10], 'labels': '"a u with\'" b c d e'},
                  1: {'bins': [0, 2, 4, 7], 'labels': 'A B C'}},
        'suffix': (False, None)
    }

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    s.colTypes[0] = Types.Ordinal
    s.colTypes[1] = Types.Ordinal
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert nan_to_None(g.to_dict()) == {
        'col1': ['a u with\'', None, 'b', 'd', 'e'],
        'col2': ['B', 'B', None, 'C', None],
        'ww': [3, 1, 'ww', '1', '1']
    }
    assert g.shape == s


def test_discretize_range_suffix():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, None, 6, None], 'ww': [3, 1, 'ww', '1', '1'],
         'col2_binss': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = RangeDiscretizer()

    tOpts = {1: {'bins': [0, 2, 4, 7], 'labels': 'A B C'}}
    op.setOptions(table=tOpts,
                  suffix=(True, '_binss'))

    tOpts[1] = {}
    assert op.getOptions() == {
        'table': {1: {'bins': [0, 2, 4, 7], 'labels': 'A B C'}},
        'suffix': (True, '_binss')
    }

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    s.colTypes[1] = Types.Numeric
    s.colTypes[3] = Types.Ordinal
    assert op.getOutputShape() == s

    g = op.execute(f)
    expected_output = {
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, None, 6, None],
        'ww': [3, 1, 'ww', '1', '1'],
        'col2_binss': ['B', 'B', None, 'C', None]  # This column must replace the original duplicate
    }
    assert nan_to_None(g.to_dict()) == expected_output
    assert g.shape == s

    # Check that output is the same as with drop
    op.setOptions(table={1: {'bins': [0, 2, 4, 7], 'labels': 'A B C'}}, suffix=(False, None))
    o = op.execute(f)
    assert expected_output['col2_binss'] == nan_to_None(o.to_dict())['col2']
    assert expected_output['col2'] != nan_to_None(o.to_dict())['col2']
    assert expected_output['ww'] == nan_to_None(o.to_dict())['ww']
    assert expected_output['col1'] == nan_to_None(o.to_dict())['col1']
    assert expected_output['col2_binss'] != nan_to_None(o.to_dict())['col2_binss']


def test_discretize_range_except():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = RangeDiscretizer()
    op.addInputShape(f.shape, 0)
    with pytest.raises(exp.OptionValidationError):
        op.setOptions(table={0: {'bins': '2'}, 1: {'bins': '3 2 1', 'labels': '2 1'}},
                      suffix=(False, ()))
    assert op.getOutputShape() is None

    with pytest.raises(exp.OptionValidationError):
        op.setOptions(table={0: {'bins': '2', 'labels': ''}, 1: {'bins': '3 2 1', 'labels': '2 1'}},
                      suffix=(False, None))

    assert op.getOutputShape() is None

    # bins must be float, labels can be whatever
    tabls = {0: {'bins': '2 3 A', 'labels': 'new 2'}}
    with pytest.raises(exp.OptionValidationError):
        op.setOptions(table=tabls, suffix=(True, 'sa'))

    assert op.getOutputShape() is None

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(table={}, suffix=(True, ''))
    a: List[Tuple[str, str]] = e.value.invalid
    assert 'noAttr' in map(lambda x: x[0], a)

    assert op.getOutputShape() is None

    with pytest.raises(exp.OptionValidationError) as ext:
        op.setOptions(table={0: {}}, suffix=(False, None))
    a: List[Tuple[str, str]] = ext.value.invalid
    assert 'notSet' in map(lambda x: x[0], a)

    assert op.getOutputShape() is None

    with pytest.raises(exp.OptionValidationError) as exc:
        op.setOptions(table={1: {'labels': ''}}, suffix=(False, ''))
    a: List[Tuple[str, str]] = exc.value.invalid
    assert 'notSet' in map(lambda x: x[0], a)

    assert op.getOutputShape() is None
    assert op.getOptions() == {
        'table': {},
        'suffix': (True, '_bins')
    }
