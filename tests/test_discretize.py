import numpy as np

from data_preprocessor import data
from data_preprocessor.operation.discretize import BinsDiscretizer, BinStrategy
from tests.utilities import nan_to_None


def test_discretize_num_uniform():
    d = {'col1': [1, -1.1, 3, 7.5, 10], 'col2': [3, 4, np.nan, 6, np.nan], 'ww': [3, 1, 'ww', '1', '1']}
    f = data.Frame(d)

    op = BinsDiscretizer()
    op.setOptions(attributes={0: {'bins': '2'}, 1: {'bins': '3'}}, strategy=BinStrategy.Uniform)

    op.addInputShape(f.shape, 0)
    s = f.shape.copy()
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert nan_to_None(g.to_dict()) == {
        'col1': [0.0, 0.0, 0.0, 1.0, 1.0],
        'col2': [0.0, 1.0, None, 2.0, None],
        'ww': [3, 1, 'ww', '1', '1']
    }
