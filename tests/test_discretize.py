import numpy as np

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.operation.discretize import BinsDiscretizer, BinStrategy
from tests.utilities import nan_to_None


def test_discretize_num_uniform():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = BinsDiscretizer()
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform,
                  drop=True)

    op.addInputShape(f.shape, 0)
    s = f.shape.copy()
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert nan_to_None(g.to_dict()) == {
        'col1': [0.0, 0.0, 0.0, 1.0, 1.0],
        'col2': [0.0, 1.0, None, 2.0, None],
        'ww': [3, 1, 'ww', '1', '1']
    }


def test_discretize_num_uniform_nondrop():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = BinsDiscretizer()
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform,
                  drop=False)

    op.addInputShape(f.shape, 0)
    s = f.shape.copy(True)
    s.col_names.append('col1_discretized')
    s.col_names.append('col2_discretized')
    s.col_types.append(Types.Numeric)
    s.col_types.append(Types.Numeric)
    s.n_columns += 2
    assert op.getOutputShape() == s

    g = op.execute(f)
    expected_output = {
        'col1_discretized': [0.0, 0.0, 0.0, 1.0, 1.0],
        'col2_discretized': [0.0, 1.0, None, 2.0, None],
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, None, 6, None],
        'ww': [3, 1, 'ww', '1', '1']
    }
    assert nan_to_None(g.to_dict()) == expected_output

    # Check that outpu is the same as with drop
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform,
                  drop=True)
    o = op.execute(f)
    assert expected_output['col1_discretized'] == nan_to_None(o.to_dict())['col1']
    assert expected_output['col2_discretized'] == nan_to_None(o.to_dict())['col2']
    assert expected_output['col1'] != nan_to_None(o.to_dict())['col1']
    assert expected_output['col2'] != nan_to_None(o.to_dict())['col2']
