import numpy as np

from dataMole import data
from dataMole.operation.scaling import MinMaxScaler, StandardScaler
from dataMole.operation.utils import numpy_equal
from tests.utilities import nan_to_None, roundValues


def test_minMaxScale():
    d = {
        'id1': ['ab', 'sa', '121', '121', 'a'],
        'id2': [1, np.nan, 0, 44, 0],
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, np.nan, 6, np.nan],
        'ww': [3, np.nan, 'ww', '1', '1']
    }
    f = data.Frame(d)
    f = f.setIndex(['id1', 'id2'])

    op = MinMaxScaler()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: {'range': (-1, 1)}, 1: {'range': (2, 4)}})
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)

    g = op.execute(f)
    expected = {
        'col1': [((x - min(d['col1'])) / (max(d['col1']) - min(d['col1']))) for x in d['col1']],
        'col2': [((x - min(d['col2'])) / (max(d['col2']) - min(d['col2']))) for x in d['col2']],
        'ww': [3, None, 'ww', '1', '1']
    }
    expected = {
        'col1': [x * (1 - (-1)) - 1 for x in expected['col1']],
        'col2': [x * (4 - 2) + 2 for x in expected['col2']],
        'ww': expected['ww']
    }
    assert nan_to_None(roundValues(g.to_dict(), 4)) == nan_to_None(roundValues(expected, 4))
    assert g.shape == s
    assert not numpy_equal(g.getRawFrame().values, f.getRawFrame().values)

    options = op.getOptions()
    assert options == {'attributes': {0: {'range': (-1, 1)}, 1: {'range': (2, 4)}}}


def test_minMaxScale_1_attr():
    d = {
        'id1': ['ab', 'sa', '121', '121', 'a'],
        'id2': [1, np.nan, 0, 44, 0],
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, np.nan, 6, np.nan],
        'ww': [3, np.nan, 'ww', '1', '1']
    }
    f = data.Frame(d)
    f = f.setIndex(['id1', 'id2'])

    op = MinMaxScaler()
    assert op.getOutputShape() is None
    op.setOptions(attributes={1: {'range': (2, 4)}})
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)

    g = op.execute(f)
    expected = {
        'col1': d['col1'],
        'col2': [((x - min(d['col2'])) / (max(d['col2']) - min(d['col2']))) for x in d['col2']],
        'ww': [3, None, 'ww', '1', '1']
    }
    expected = {
        'col1': expected['col1'],
        'col2': [x * (4 - 2) + 2 for x in expected['col2']],
        'ww': expected['ww']
    }
    assert nan_to_None(roundValues(g.to_dict(), 4)) == nan_to_None(roundValues(expected, 4))
    assert g.shape == s
    assert not numpy_equal(g.getRawFrame().values, f.getRawFrame().values)


def test_minMaxScale_2_attr_equal_ange():
    d = {
        'id2': [1, np.nan, 0, 44, 0],
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, np.nan, 6, np.nan],
        'ww': [3, np.nan, 'ww', '1', '1']
    }
    f = data.Frame(d)
    f = f.setIndex('id2')

    op = MinMaxScaler()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: {'range': (-1.1, 9.5)}, 1: {'range': (-1.1, 9.5)}})
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)

    g = op.execute(f)
    expected = {
        'col1': [((x - min(d['col1'])) / (max(d['col1']) - min(d['col1']))) for x in d['col1']],
        'col2': [((x - min(d['col2'])) / (max(d['col2']) - min(d['col2']))) for x in d['col2']],
        'ww': [3, None, 'ww', '1', '1']
    }
    expected = {
        'col1': [x * (9.5 - (-1.1)) - 1.1 for x in expected['col1']],
        'col2': [x * (9.5 - (-1.1)) - 1.1 for x in expected['col2']],
        'ww': expected['ww']
    }
    assert nan_to_None(roundValues(g.to_dict(), 4)) == nan_to_None(roundValues(expected, 4))
    assert g.shape == s
    assert not numpy_equal(g.getRawFrame().values, f.getRawFrame().values)


def test_standardScale():
    d = {
        'id1': ['ab', 'sa', '121', '121', 'a'],
        'id2': [1, np.nan, 0, 44, 0],
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, np.nan, 6, np.nan],
        'ww': [3, np.nan, 'ww', '1', '1']
    }
    f = data.Frame(d)
    f = f.setIndex(['id1', 'id2'])

    op = StandardScaler()
    assert op.getOutputShape() is None
    op.setOptions(attributes={0: None, 1: None})
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)

    g = op.execute(f)
    expected = {
        'col1': [((x - np.nanmean(d['col1'])) / np.nanstd(d['col1'])) for x in d['col1']],
        'col2': [((x - np.nanmean(d['col2'])) / np.nanstd(d['col2'])) for x in d['col2']],
        'ww': [3, None, 'ww', '1', '1']
    }
    assert nan_to_None(roundValues(g.to_dict(), 4)) == nan_to_None(roundValues(expected, 4))
    assert g.shape == s
    assert not numpy_equal(g.getRawFrame().values, f.getRawFrame().values)

    options = op.getOptions()
    assert options == {'attributes': {0: None, 1: None}}


def test_standardScale_1_attr():
    d = {
        'id1': ['ab', 'sa', '121', '121', 'a'],
        'id2': [1, np.nan, 0, 44, 0],
        'col1': [1, -1.1, 3, 7.5, 10],
        'col2': [3, 4, np.nan, 6, np.nan],
        'ww': [3, np.nan, 'ww', '1', '1']
    }
    f = data.Frame(d)
    f = f.setIndex(['id1', 'id2'])

    op = StandardScaler()
    assert op.getOutputShape() is None
    op.setOptions(attributes={1: None})
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)

    g = op.execute(f)
    expected = {
        'col1': d['col1'],
        'col2': [((x - np.nanmean(d['col2'])) / np.nanstd(d['col2'])) for x in d['col2']],
        'ww': [3, None, 'ww', '1', '1']
    }
    assert nan_to_None(roundValues(g.to_dict(), 4)) == nan_to_None(roundValues(expected, 4))
    assert g.shape == s
    assert not numpy_equal(g.getRawFrame().values, f.getRawFrame().values)


def test_standardScale_1_attr_all_nan():
    d = {
        'id1': ['ab', 'sa', '121', '121', 'a'],
        'id2': [1, np.nan, 0, 44, 0],
        'col1': [1.0, -1.1, 3.0, 7.5, 10.0],
        'col2': [np.nan, np.nan, np.nan, np.nan, np.nan],
        'ww': [3, np.nan, 'ww', '1', '1']
    }
    f = data.Frame(d)
    f = f.setIndex(['id1', 'id2'])

    op = StandardScaler()
    assert op.getOutputShape() is None
    op.setOptions(attributes={1: None})
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    assert op.getOutputShape() == s

    op.removeInputShape(0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)

    g = op.execute(f)
    expected = {
        'col1': d['col1'],
        'col2': [((x - np.nanmean(d['col2'])) / np.nanstd(d['col2'])) for x in d['col2']],
        'ww': [3, None, 'ww', '1', '1']
    }
    assert nan_to_None(roundValues(g.to_dict(), 4)) == nan_to_None(roundValues(expected, 4))
    assert g.shape == s
