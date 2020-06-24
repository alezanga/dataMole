import numpy as np

from data_preprocessor import data
from data_preprocessor.operation.cleaner import RemoveBijections
from tests.utilities import nan_to_None


def test_remove_bijections():
    op = RemoveBijections()

    d = {'col1': [1.0, 2.0, 3.0, np.nan, 10.0], 'col2': [3.0, 4.0, np.nan, 6.0, np.nan],
         'col3': ['q', '2', 'c', '4', 'x'],
         'col11': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    f = data.Frame(d)

    op.addInputShape(f.shape, 0)
    op.setOptions(attributes={1: None, 0: None, 2: None, 3: None})

    g = op.execute(f)
    expected = d
    del expected['col11']
    assert nan_to_None(expected) == nan_to_None(g.to_dict())
