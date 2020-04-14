import pandas
import pytest
from numpy import int64

from data_preprocessor.data import Frame, Shape


def test_apply():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = Frame(d)
    f['new_col'] = f.apply(lambda row: row['col1'] * row['col2'])

    f.head()
    assert f['new_col'].to_dict() == {'new_col': [3, 8, 15, 24, 0]}


def test_boolean_indexing():
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = Frame(d)
    f['type'] = f.apply(
        lambda x: ((x['col1'] - int(x['col1']) != 0) or (x['col2'] - int(x['col2']) != 0)))
    f = f.query('(col1 > 4) or type')
    f.head()
    heads = f.columns
    heads.remove('type')
    f = f[heads]
    assert f.to_dict() == {'col1': [0.5, 10], 'col2': [5, 0]}


def test_reorder():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f = f[['col2', 'col1', 'col3']]
    assert list(f.to_dict().keys()) == ['col2', 'col1', 'col3']


def test_rename():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    names = f.columns
    names[1] = 'new'
    f.columns = names
    assert f.columns == ['col1', 'new', 'col3']


def test_rename_with_int():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    names = f.columns
    names[1] = 2
    f.columns = names
    assert f.columns == ['col1', 2, 'col3']


def test_rename_excep():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    names = f.columns
    names.append('1')
    with pytest.raises(ValueError):
        f.columns = names


def test_typing():
    a = 4
    b = pandas.DataFrame()
    d: int64 = 12
    c = Frame()
    assert isinstance(type(a), type) and isinstance(type(b), type) and issubclass(type(c), Frame) and \
           isinstance(type(c), type) and isinstance(type(d), type)


def test_shape():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    s = Shape()
    s.n_rows = 5
    s.n_columns = 3
    s.index = None
    s.col_name_type = {
        'col1': 'int',
        'col2': 'int',
        'col3': 'str'
    }

    assert f.shape == s


def test_shape_index():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)
    f.set_index('col3')

    # Desired shape obj
    s = Shape()
    s.n_rows = 5
    s.n_columns = 2
    s.index = 'col3'
    s.col_name_type = {
        'col1': 'float',
        'col3': 'str',
        'col2': 'int'
    }
