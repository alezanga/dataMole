import pandas as pd
import pytest
from numpy import int64
import numpy as np

from data_preprocessor.data import Frame, Shape


def test_apply():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = Frame(d)

    f['new_col'] = f.apply(lambda row: row['col1'] * row['col2'])

    print(f.head())
    assert f.columnsAt('new_col').to_dict() == {'new_col': [3, 8, 15, 24, 0]}


def test_boolean_indexing():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = Frame(d)
    f['type'] = f.apply(
        lambda x: ((x['col1'] - int(x['col1']) != 0) or (x['col2'] - int(x['col2']) != 0)))
    f = f.query('(col1 > 4) or type')
    f.head()
    heads = f.colnames
    heads.remove('type')
    f = f.columnsAt(heads)
    assert f.to_dict() == {'col1': [0.5, 10], 'col2': [5, 0]}


def test_reorder():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.columnsAt(['col2', 'col1', 'col3'])
    assert list(f.to_dict().keys()) == ['col2', 'col1', 'col3']


def test_rename():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    g = f.rename({'col2': 'new'})
    assert g.colnames == ['col1', 'new', 'col3'] and f.colnames == ['col1', 'col2', 'col3']


def test_rename_bis():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    g = f.rename(['cola', '21eeds', 'ij_'])
    assert g.colnames == ['cola', '21eeds', 'ij_'] and f.colnames == ['col1', 'col2', 'col3']


def test_rename_excep():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    names = f.colnames
    names.append('1')
    with pytest.raises(ValueError):
        f.rename(names)


# COLUMNS AT

def test_columnsAt1():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.columnsAt(cols=2)
    assert a.to_dict() == {'col3': ['q', '2', 'c', '4', 'x']}


def test_columnsAt2():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.columnsAt(cols=[2, 0])
    assert a.to_dict() == {'col3': ['q', '2', 'c', '4', 'x'], 'col1': [1, 2, 3, 4, 10]}


def test_columnsAt3():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.columnsAt(slice('col2'))
    assert a.to_dict() == {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0]}


def test_columnsAt3bis():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.columnsAt('col1')
    b = f.columnsAt(['col1'])
    assert a.to_dict() == {'col1': [1, 2, 3, 4, 10]} and a == b


def test_columnsAt4():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.columnsAt(slice(-2, None))
    print(a)
    assert a.to_dict() == {'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}


def test_columnsAt5():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.columnsAt(slice(-1, None, -2))
    print(a)
    assert a.to_dict() == {'col1': [1, 2, 3, 4, 10], 'col3': ['q', '2', 'c', '4', 'x']}


def test_columnsAt6():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.columnsAt(['col3', 'col1'])
    print(a)
    assert a.to_dict() == {'col1': [1, 2, 3, 4, 10], 'col3': ['q', '2', 'c', '4', 'x']}


def test_columnsAt_exc():
    with pytest.raises(ValueError):
        d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
        f = Frame(d)
        f.columnsAt([])


def test_columnsAt_exc2():
    with pytest.raises(TypeError):
        f = Frame({})
        f.columnsAt(slice())


def test_columnsAt_exc3():
    with pytest.raises(TypeError):
        f = Frame({})
        f.columnsAt({-1: 'a'})


# ROWS AT

def test_rowsAt1():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    # Single element: format different
    a = f.rowsAt(2)
    assert a.to_dict() == {2: [3, 5, 'c']}


def test_rowsAt1List():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    # If it's a list format is different
    a = f.rowsAt([2])
    assert a.to_dict() == {'col1': [3], 'col2': [5], 'col3': ['c']}


def test_rowsAtLast():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.rowsAt(-1)
    assert a.to_dict() == {4: [10, 0, 'x']}


def test_rowsAt2():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.rowsAt(rows=[0, 2])
    assert a.to_dict() == {'col1': [1, 3], 'col2': [3, 5], 'col3': ['q', 'c']}


def test_rowsAt_exc():
    with pytest.raises(TypeError):
        d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
        f = Frame(d)
        f.rowsAt(slice('col2'))


def test_rowsAt_colsAt():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.rowsAt(slice(-2, None, -2)).columnsAt(slice(-2, None))
    print(a)
    assert a.to_dict() == {'col2': [6, 4], 'col3': ['4', '2']}


def test_rowsAt5():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.rowsAt(slice(-1, None, -2))
    print(a)
    assert a.to_dict() == {'col1': [10, 3, 1], 'col2': [0, 5, 3], 'col3': ['x', 'c', 'q']}


def test_rowsAt6():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    # Exclude stop element
    a = f.rowsAt(slice(2))
    print(a)
    assert a.to_dict() == {'col1': [1, 2], 'col2': [3, 4], 'col3': ['q', '2']}


def test_rowsAt7():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    # Exclude stop element
    a = f.rowsAt(slice(None, -1, 2))
    print(a)
    assert a.to_dict() == {'col1': [1, 3], 'col2': [3, 5], 'col3': ['q', 'c']}


def test_rowsAt_exc2():
    with pytest.raises(TypeError):
        f = Frame({})
        # Doesn't accept list of strings
        f.rowsAt(['', 1])


# ROWS AT INDEX

def test_rowsAtIndex():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col2')
    a = f.rowsAtIndex(slice(None, 0, 2))
    assert a.to_dict() == {'col1': [1, 3, 10], 'col2': [3, 5, 0], 'col3': ['q', 'c', 'x']}


def test_rowsAtIndex2():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col3')
    a = f.rowsAtIndex(['q'])
    assert a.to_dict() == {'col1': [1], 'col2': [3], 'col3': ['q']}


def test_rowsAtIndex3():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col3')
    a = f.rowsAtIndex(['q', 'x'])
    assert a.to_dict() == {'col1': [1, 10], 'col2': [3, 0], 'col3': ['q', 'x']}


def test_rowsAtIndex4():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col3')
    a = f.rowsAtIndex(slice('4', '2', -1))
    assert a.to_dict() == {'col1': [4, 3, 2], 'col2': [6, 5, 4], 'col3': ['4', 'c', '2']}


def test_rowsAtIndex5():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col3')
    a = f.rowsAtIndex(slice('4', None))
    assert a.to_dict() == {'col1': [4, 10], 'col2': [6, 0], 'col3': ['4', 'x']}


def test_rowsAtIndexDefault():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.rowsAtIndex(1)
    assert a.to_dict() == {1: [2, 4, '2']}


def test_rowsAtIndex_exc():
    with pytest.raises(TypeError):
        d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
        f = Frame(d)
        f.rowsAtIndex(slice())


# DROP COLUMNS
def test_dc1():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.dropCols([1])
    b = f.dropCols(1)
    assert a.to_dict() == {'col1': [1, 2, 3, 4, 10], 'col3': ['q', '2', 'c', '4', 'x']} and a == b


def test_dc2():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.dropCols(['col1', 'col2'])
    b = f.dropCols([0, 1])
    assert a.to_dict() == {'col3': ['q', '2', 'c', '4', 'x']} and a == b


def test_dc3():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col1')
    a = f.dropCols('col1').rowsAtIndex([1, 2, 4])
    b = f.dropCols(['col1']).rowsAtIndex([1, 2, 4])
    assert a.to_dict() == {'col2': [3, 4, 6], 'col3': ['q', '2', '4']} and a == b


# DROP ROWS

def test_dr1():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col1')
    a = f.dropRows([2], by='number').columnsAt('col2')
    b = f.dropRows(2, by='number').columnsAt('col2')
    assert a.to_dict() == {'col2': [3, 4, 6, 0]} and a == b


def test_dr2():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col1')
    a = f.dropRows([2], by='index').columnsAt('col2')
    b = f.dropRows(2, by='index').columnsAt('col2')
    assert a.to_dict() == {'col2': [3, 5, 6, 0]} and a == b


def test_dr3():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col1')
    a = f.dropRows([2, 4, 1], by='index')
    assert a.to_dict() == {'col1': [3, 10], 'col2': [5, 0], 'col3': ['c', 'x']}


def test_dr4():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col1')
    a = f.dropRows([2, 4, 1], by='number')
    assert a.to_dict() == {'col1': [1, 4], 'col2': [3, 6], 'col3': ['q', '4']}


def test_dr_exc():
    with pytest.raises(KeyError):
        d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
        f = Frame(d)
        f = f.setIndex('col1')
        f.dropRows([2, 4, 5], by='index')


def test_dr_exc2():
    with pytest.raises(ValueError):
        d = {'col1': [1, 2, 3, 4, 10]}
        f = Frame(d)
        # Raise exc for unsupported argument
        f.dropRows([2, 4, 5], by='aa')


# REPLACE

def test_replace1():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col1')
    a = f.replace(['q', 4], -1)
    assert a.to_dict() == {'col1': [1, 2, 3, -1, 10], 'col2': [3, -1, 5, 6, 0],
                           'col3': [-1, '2', 'c', '4', 'x']}


def test_replace2():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.replace({1: -1, 'q': 77, 5: 'e'})
    assert a.to_dict() == {'col1': [-1, 2, 3, 4, 10], 'col2': [3, 4, 'e', 6, 0],
                           'col3': [77, '2', 'c', '4', 'x']}


def test_replaceRegex1():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.replaceRegex('\\d+', 'num')
    assert a.to_dict() == {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', 'num',
                                                                                       'c', 'num', 'x']}


# MEAN & STD

def test_mean():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.mean(column='col1')
    from statistics import mean
    assert a == mean(d['col1'])


def test_mean_str():
    with pytest.raises(TypeError):
        d = {'col1': [1, 2, 3, 4, 10], 'col2': ['3', '4', '5', '6', '0'],
             'col3': ['q', '2', 'c', '4', 'x']}
        f = Frame(d)
        f.mean(column='col2')


def test_std():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    a = f.std(column='col1')
    from statistics import stdev
    assert a == stdev(d['col1'])


# TYPING

def test_typing():
    a = 4
    b = pd.DataFrame()
    d: int64 = 12
    c = Frame()
    assert isinstance(type(a), type) and isinstance(type(b), type) and issubclass(type(c), Frame) and \
           isinstance(type(c), type) and isinstance(type(d), type)


# SHAPE

def test_shape():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    s = Shape()
    s.n_rows = 5
    s.n_columns = 3
    s.index = None
    s.col_names = ['col1', 'col2', 'col3']
    s.col_types = ['numeric', 'numeric', 'str']

    assert f.shape == s


def test_setIndex():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    h = f.setIndex('col3')
    g = f.setIndex(2)
    assert h.shape == g.shape


def test_shape_index():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f.setIndex('col3')

    # Desired shape obj
    s = Shape()
    s.n_rows = 5
    s.n_columns = 3
    s.index = 'col3'
    s.col_names = ['col1', 'col2', 'col3']
    s.col_types = ['numeric', 'numeric', 'str']

    assert f.shape == s


def test_fromShape():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'cold': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = Frame(d)
    f = f.setIndex('col3')

    g = Frame.fromShape(f.shape)

    s = Shape()
    s.n_rows = 1
    s.n_columns = 4
    s.index = 'col3'
    s.col_names = ['col1', 'col2', 'col3', 'cold']
    s.col_types = ['numeric', 'numeric', 'str', 'date']
    assert g.shape == s
