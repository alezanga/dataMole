import copy

import numpy as np

from dataMole import data
from dataMole.operation.cleaner import RemoveBijections
from tests.utilities import nan_to_None


def test_remove_bijections():
    op = RemoveBijections()

    d = {'col1': [1.0, 2.0, 3.0, np.nan, 10.0], 'col2': [3.0, 4.0, np.nan, 6.0, np.nan],
         'col3': ['q', '2', 'c', '4', 'x'],
         'col11': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    f = data.Frame(d)

    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    assert op.getOptions() == {
        'attributes': dict()
    }

    oo = {1: None, 0: None, 2: None, 3: None}
    op.setOptions(attributes=oo)
    assert op.getOutputShape() is None
    assert op.needsInputShapeKnown() is True
    assert op.isOutputShapeKnown() is False
    assert op.getOptions() == {
        'attributes': {1: None, 0: None, 3: None, 2: None}
    }
    oo[1] = 'ss'
    assert op.getOptions() == {
        'attributes': {1: None, 0: None, 3: None, 2: None}
    }

    g = op.execute(f)
    expected = copy.deepcopy(d)
    del expected['col11']
    assert nan_to_None(expected) == nan_to_None(g.to_dict())


def test_remove_bijections_with_nan():
    op = RemoveBijections()

    d = {'col1': [1.0, 2.0, 3.0, np.nan, 10.0], 'col2': [3.0, 4.0, np.nan, 6.0, np.nan],
         'col3': ['q', '2', 'c', '4', np.nan],
         'col11': ['q', '2', 'c', '4', np.nan],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    f = data.Frame(d)

    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    assert op.getOptions() == {
        'attributes': dict()
    }

    oo = {1: None, 0: None, 2: None, 3: None}
    op.setOptions(attributes=oo)
    assert op.getOutputShape() is None
    assert op.needsInputShapeKnown() is True
    assert op.isOutputShapeKnown() is False
    assert op.getOptions() == {
        'attributes': {1: None, 0: None, 3: None, 2: None}
    }
    oo[1] = 'ss'
    assert op.getOptions() == {
        'attributes': {1: None, 0: None, 3: None, 2: None}
    }

    g = op.execute(f)
    expected = copy.deepcopy(d)
    del expected['col11']
    assert nan_to_None(expected) == nan_to_None(g.to_dict())
