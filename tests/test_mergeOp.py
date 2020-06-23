import pandas as pd
import pytest

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.operation.interface.exceptions import *
from data_preprocessor.operation.merge_values import MergeValuesOp
from tests.utilities import nan_to_None


def test_exception():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)
    op = MergeValuesOp()

    op.addInputShape(f.shape, 0)

    with pytest.raises(OptionValidationError):
        op.setOptions(table={
            1: {
                'replace': '7; h',
                'values': '3 4 5; 2'
            }},
            inverted=False)

    with pytest.raises(OptionValidationError):
        op.setOptions(table={
            1: {
                'replace': '7;    8;1',
                'values': '3 4 5; 2'
            }},
            inverted=False)


def test_merge_numeric():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)
    op = MergeValuesOp()

    op.addInputShape(f.shape, 0)
    op.setOptions(table={1: {'values': '1.0 3.0 4.0;  6  0', 'replace': '-1;-2'},
                         0: {'values': '1 4', 'replace': '7'}},
                  inverted=False)
    s = f.shape.copy()
    assert op.getOutputShape() == s

    g = op.execute(f)

    assert g != f and g.shape == s
    assert g.to_dict() == {
        'col1': [7.0, 2.0, 3.0, 7.0, 10.0], 'col2': [-1.0, -1.0, 5.0, -2.0, -2.0],
        'col3': ['q', '2', 'c', '4', 'x'],
        'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}


def test_merge_numeric_inverted():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)
    op = MergeValuesOp()

    op.addInputShape(f.shape, 0)
    # Substitution doesn't make sense, but it's test
    op.setOptions(table={1: {'values': '1.0 3.0 4.0;  6  0', 'replace': '-1;-2'},
                         0: {'values': '1 4', 'replace': '7'}},
                  inverted=True)
    s = f.shape.copy()
    assert op.getOutputShape() == s

    g = op.execute(f)

    assert g != f and g.shape == s
    assert g.to_dict() == {
        'col1': [1.0, 7.0, 7.0, 4.0, 7.0], 'col2': [-2.0, -2.0, -2.0, -2.0, -2.0],
        'col3': ['q', '2', 'c', '4', 'x'],
        'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}


def test_merge_category():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(["3", "4", "5", "6", "0"]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)
    op = MergeValuesOp()

    op.addInputShape(f.shape, 0)
    op.setOptions(table={
        1: {
            'values': '4 0; 3; 6',
            'replace': '0;  1; nan'
        }},
        inverted=False)

    s = f.shape.copy()
    assert op.getOutputShape() == s
    assert s.col_types[1] == Types.Nominal

    g = op.execute(f)

    assert nan_to_None(g.to_dict()) == {'col1': [1, 2, 3, 4.0, 10],
                                        'col2': ["1", "0", "5", None, "0"],
                                        'col3': ['q', '2', 'c', '4', 'x'],
                                        'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994',
                                                 '12-12-2012']}
    assert g != f and g.shape == s


def test_merge_category_inverted():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(["3", "4", "5", "6", "0"]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)
    op = MergeValuesOp()

    op.addInputShape(f.shape, 0)
    op.setOptions(table={
        1: {
            'values': '4 0; 0',
            'replace': 'val;  NAN'
        }},
        inverted=True)

    s = f.shape.copy()
    assert op.getOutputShape() == s
    assert s.col_types[1] == Types.Nominal

    g = op.execute(f)

    assert nan_to_None(g.to_dict()) == {'col1': [1, 2, 3, 4.0, 10],
                                        'col2': [None, None, None, None, "0"],
                                        'col3': ['q', '2', 'c', '4', 'x'],
                                        'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994',
                                                 '12-12-2012']}
    assert g != f and g.shape == s


def test_merge_string():
    d = {'cowq': [1, 2, None, 4.0, None], 'col3': ['q', '2', 'c', '4', 'q']}
    f = data.Frame(d)
    f = f.setIndex('col3')

    op = MergeValuesOp()
    op.addInputShape(f.shape, 0)
    op.setOptions(table={
        1: {
            'values': 'q 2; nAn',
            'replace': '-1;-2'}},
        inverted=False)

    s = f.shape.copy()
    assert f.shape.col_types[1] == Types.String
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert g.shape == f.shape
    ff = {'cowq': [1.0, 2.0, None, 4.0, None], 'col3': ["-1", "-1", "c", "4", "-1"]}
    assert nan_to_None(g.to_dict()) == ff


def test_merge_nan():
    d = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(["3", "4", "5", "6", "0"]),
         'col3': ['q', '2', 'c', '4', 'x']}
    f = data.Frame(d)
    f = f.setIndex('col3')

    op = MergeValuesOp()
    op.addInputShape(f.shape, 0)
    op.setOptions(table={
        1: {
            'values': 'hello 2 6 0; 3',
            'replace': 'NAN; nan'},
        0: {
            'values': '2 4 10',
            'replace': 'naN'}},
        inverted=False)

    s = f.shape.copy()
    assert f.shape.col_types[1] == Types.Nominal
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert g.shape == f.shape
    ff = {'cowq': [1, None, 3, None, None], 'col2': [None, "4", "5", None, None],
          'col3': ['q', '2', 'c', '4', 'x']}
    assert nan_to_None(g.to_dict()) == ff


def test_merge_from_nan():
    d = {'cowq': [1, 2, None, 4.0, None], 'col2': pd.Categorical(["3", "4", "5", "6", "0"]),
         'col3': ['q', '2', 'c', '4', 'x']}
    f = data.Frame(d)
    f = f.setIndex('col3')

    op = MergeValuesOp()
    op.addInputShape(f.shape, 0)
    op.setOptions(table={
        0: {
            'values': 'Nan 2.0;4.0',
            'replace': '-1;-2'}},
        inverted=False)

    s = f.shape.copy()
    assert f.shape.col_types[1] == Types.Nominal
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert g.shape == f.shape
    ff = {'cowq': [1.0, -1.0, -1.0, -2.0, -1.0], 'col2': ["3", "4", "5", "6", "0"],
          'col3': ['q', '2', 'c', '4', 'x']}
    assert nan_to_None(g.to_dict()) == ff


def test_merge_index_val():
    d = {'cowq': [1, 2, 3, 4.0, 10], 'col2': pd.Categorical(["3", "4", "5", "6", "0"]),
         'col3': ['q', '2', 'c', '4', 'x'],
         'date': pd.Series(['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    f = data.Frame(d)
    f = f.setIndex('col2')

    op = MergeValuesOp()
    op.addInputShape(f.shape, 0)
    op.setOptions(table={1: {
        'values': '3 4;  6  0', 'replace': 'h; nan'}
    }, inverted=False)

    s = f.shape.copy()
    os = op.getOutputShape()
    assert f.shape.col_types[1] == Types.Nominal == os.col_types[1]
    assert os == s

    g = op.execute(f)
    assert g.shape == f.shape
    assert nan_to_None(g.columnsAt('col2').to_dict()) == {'col2': ["h", "h", "5", None, None]}
