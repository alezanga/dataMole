from typing import List, Tuple

import numpy as np
import pytest

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.operation.discretize import BinsDiscretizer, BinStrategy, RangeDiscretizer
from data_preprocessor import exceptions as exp
from tests.utilities import nan_to_None


def test_discretize_num_uniform():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = BinsDiscretizer()
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform,
                  drop=True)

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    s.colTypes[0] = Types.Nominal
    s.colTypes[1] = Types.Nominal
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert nan_to_None(g.to_dict()) == {
        'col1': ['0.0', '0.0', '0.0', '1.0', '1.0'],
        'col2': ['0.0', '1.0', None, '2.0', None],
        'ww': [3, 1, 'ww', '1', '1']
    }
    assert g.shape == s


def test_discretize_num_uniform_nondrop():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = BinsDiscretizer()
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform,
                  drop=False)

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    s.colNames.append('col1_discretized')
    s.colNames.append('col2_discretized')
    s.colTypes.append(Types.Nominal)
    s.colTypes.append(Types.Nominal)
    assert op.getOutputShape() == s

    g = op.execute(f)
    expected_output = {
        'col1_discretized': ['0.0', '0.0', '0.0', '1.0', '1.0'],
        'col2_discretized': ['0.0', '1.0', None, '2.0', None],
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, None, 6, None],
        'ww': [3, 1, 'ww', '1', '1']
    }
    assert nan_to_None(g.to_dict()) == expected_output
    assert g.shape == s

    # Check that output is the same as with drop
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform,
                  drop=True)
    o = op.execute(f)
    assert expected_output['col1_discretized'] == nan_to_None(o.to_dict())['col1']
    assert expected_output['col2_discretized'] == nan_to_None(o.to_dict())['col2']
    assert expected_output['col1'] != nan_to_None(o.to_dict())['col1']
    assert expected_output['col2'] != nan_to_None(o.to_dict())['col2']


def test_discretize_range_drop():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = RangeDiscretizer()

    op.setOptions(table={0: {'bins': '0 2 4 6 8 10', 'labels': '"a u with\'" b c d e'},
                         1: {'bins': '0 2 4 7', 'labels': 'A B C'}},
                  drop=True)

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


def test_discretize_range_nodrop():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, None, 6, None], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = RangeDiscretizer()

    op.setOptions(table={1: {'bins': '0 2 4 7', 'labels': 'A B C'}},
                  drop=False)

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    s.colTypes[1] = Types.Numeric
    s.colNames.append('col2_bins')
    s.colTypes.append(Types.Ordinal)
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert nan_to_None(g.to_dict()) == {
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, None, 6, None],
        'ww': [3, 1, 'ww', '1', '1'],
        'col2_bins': ['B', 'B', None, 'C', None]
    }
    assert g.shape == s


def test_discretize_range_except():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = RangeDiscretizer()
    op.addInputShape(f.shape, 0)
    with pytest.raises(exp.OptionValidationError):
        op.setOptions(table={0: {'bins': '2'}, 1: {'bins': '3 2 1', 'labels': '2 1'}},
                      drop=True)

    with pytest.raises(exp.OptionValidationError):
        op.setOptions(table={0: {'bins': '2', 'labels': ''}, 1: {'bins': '3 2 1', 'labels': '2 1'}},
                      drop=True)

    # bins must be float, labels can be whatever
    with pytest.raises(exp.OptionValidationError):
        op.setOptions(table={0: {'bins': '2 3 A', 'labels': 'new 2'}},
                      drop=False)

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(table={}, drop=False)
    a: List[Tuple[str, str]] = e.value.invalid
    assert 'noAttr' in map(lambda x: x[0], a)

    with pytest.raises(exp.OptionValidationError) as ext:
        op.setOptions(table={0: {}}, drop=True)
    a: List[Tuple[str, str]] = ext.value.invalid
    assert 'notSet' in map(lambda x: x[0], a)

    with pytest.raises(exp.OptionValidationError) as exc:
        op.setOptions(table={1: {'labels': ''}}, drop=True)
    a: List[Tuple[str, str]] = exc.value.invalid
    assert 'notSet' in map(lambda x: x[0], a)
