import numpy as np

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.operation.remove_nan import RemoveNanRows, RemoveNanColumns


# Remove rows

def test_nan_noremove():
    d = {'col1': [1, 2, 3, np.nan, 10], 'col2': [3, 4, np.nan, 6, np.nan],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)

    op = RemoveNanRows()
    op.setOptions(number=1, percentage=None)

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    g = op.execute(f)

    assert g == f and g.shape == s and g is not f


def test_nan_removerows_bynum():
    d = {'col1': [1, 2, 3, np.nan, 10], 'col2': [3, 4, np.nan, np.nan, np.nan],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)

    op = RemoveNanRows()
    op.setOptions(number=1, percentage=None)

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    g = op.execute(f)

    assert g != f and g.shape == s
    assert g.nRows == 4


def test_nan_removerows_byperc():
    d = {'col1': [1, 2, 3, np.nan, 10], 'col2': [3, 4, np.nan, np.nan, np.nan],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)

    op = RemoveNanRows()
    op.setOptions(number=12121, percentage=0.3)

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    g = op.execute(f)

    assert g != f and g.shape == s
    assert g.nRows == 4

    op.setOptions(percentage=0.5, number=1)
    g = op.execute(f)
    assert g == f and g.nRows == 5


def test_hasOptions():
    op = RemoveNanRows()
    assert op.hasOptions() is False

    op.setOptions(number=12121, percentage=0.3)
    assert op.hasOptions() is True

    op._RemoveNanRows__thresholdPercentage = 0.2
    op._RemoveNanRows__thresholdNumber = 123
    assert op.hasOptions() is False

    op._RemoveNanRows__thresholdPercentage = None
    assert op.hasOptions() is True

    # Same for column
    op1 = RemoveNanColumns()
    op1._RemoveNanColumns__thresholdPercentage = 0.2
    op1._RemoveNanColumns__thresholdNumber = 123
    assert op1.hasOptions() is False

    op1._RemoveNanColumns__thresholdNumber = None
    assert op1.hasOptions() is True


# Remove columns

def test_remove_column():
    op = RemoveNanColumns()
    assert op.hasOptions() is False

    d = {'col1': [1, 2, 3, np.nan, 10], 'col2': [3, 4, np.nan, np.nan, np.nan],
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', None, '21-11-1995', '22-06-1994', '12-12-2012']}
    # None is same as nan
    f = data.Frame(d)
    f = f.setIndex('col1')

    op.setOptions(number=1, percentage=0.3)

    op.addInputShape(f.shape, 0)

    g = op.execute(f)

    assert g != f and g.shape != f.shape
    assert g.nRows == 5 == f.nRows
    assert g.shape.colNames == ['col3', 'date']
    assert g.shape.colTypes == [Types.String, Types.String]

    op.setOptions(percentage=None, number=3)
    g = op.execute(f)
    assert g == f and g.nRows == 5
    assert g.shape == f.shape

    op.setOptions(percentage=None, number=0)  # remove all cols with > 0 nan
    g = op.execute(f)
    assert g != f and g.nRows == 5
    # Removes also date because of None
    assert g.to_dict() == {'col3': ['q', '2', 'c', '4', 'x']}
    assert g.shape.colTypes == [Types.String]

    op.setOptions(percentage=0.6, number=0)  # remove nothing
    g = op.execute(f)
    assert g == f and g.nRows == 5
    # Removes also date because of None
    assert g.shape == f.shape

    op.setOptions(percentage=0.59, number=0)  # remove col2
    g = op.execute(f)
    assert g != f and g.nRows == 5
    # Removes also date because of None
    s = f.shape.clone()
    i = s.colNames.index('col2')
    del s.colTypes[i]
    del s.colNames[i]
    s.index = ['col1']
    assert g.shape == s
