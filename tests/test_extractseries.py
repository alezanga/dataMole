import numpy as np
import pytest

from data_preprocessor import data, exceptions as exp
from data_preprocessor.data.types import Types
from data_preprocessor.operation.extractseries import ExtractTimeSeries
from tests.mocks import WorkbenchModelMock
from tests.utilities import nan_to_None


def test_execute():
    d = {'id': ['hiab', 'gine', 'hiac', 'hiaa', 'hiad'],
         'diab1': [2.3, 3.4, 10.2, 14.6, 66.3],
         'diab2': [3, 4, np.nan, 6, np.nan],
         'new1': ['cat1', 'cat2', 'ww', '1', '10']}
    e = {'id': ['hiab', 'hiae', 'hiac', 'hiaa', 'hiad'],
         'diab4': [12, np.nan, 21.2, 13.45, 1.02],
         'diab3': [1.0, -12, 2.3, 4.1, 5.6],
         'newt': [0, 0, 1, 0, 0]}
    f = data.Frame(d)
    g = data.Frame(e)
    f = f.setIndex('id')
    g = g.setIndex('id')
    fShape = f.shape.clone()
    gShape = g.shape.clone()
    w = WorkbenchModelMock()
    w.setDataframeByName('frameF', f)
    w.setDataframeByName('frameG', g)

    assert g.getRawFrame().index.name == 'id'
    assert f.getRawFrame().index.name == 'id'

    op = ExtractTimeSeries(w)

    timeLabels = ['wave1', 'wave2', 'wave3', 'wave4']

    options = {
        'diab': [('frameG', 0, 3), ('frameF', 1, 1), ('frameF', 0, 0), ('frameG', 1, 2)],
        'other': [('frameF', 2, 0), ('frameF', 1, 1), ('frameG', 2, 2), ('frameF', 0, 3)]
    }

    op.setOptions(series=options, time=timeLabels, outName='frameR')

    # Check for side effects
    options['diab'] = []
    assert op._ExtractTimeSeries__timeLabels is not timeLabels
    assert op._ExtractTimeSeries__series is not options
    assert op._ExtractTimeSeries__series == {
        'diab': [('frameG', 0, 3), ('frameF', 1, 1), ('frameF', 0, 0), ('frameG', 1, 2)],
        'other': [('frameF', 2, 0), ('frameF', 1, 1), ('frameG', 2, 2), ('frameF', 0, 3)]
    }

    op.execute()

    assert w.getDataframeModelByName('frameF').frame.shape == fShape
    assert w.getDataframeModelByName('frameG').frame.shape == gShape
    r: data.Frame = w.getDataframeModelByName('frameR').frame

    rr = r.getRawFrame()
    rr_dict = {k: gr.to_dict(orient='records') for k, gr in rr.groupby(level=0)}
    assert {k: sorted(v, key=lambda rec: rec['time']) for k, v in nan_to_None(rr_dict).items()} == {
        'hiaa': [
            {'diab': 14.60, 'other': '1', 'time': 'wave1'},
            {'diab': 6.000, 'other': 6.00, 'time': 'wave2'},
            {'diab': 4.100, 'other': 0.00, 'time': 'wave3'},
            {'diab': 13.45, 'other': 14.6, 'time': 'wave4'}],
        'hiab': [
            {'diab': 2.30, 'other': 'cat1', 'time': 'wave1'},
            {'diab': 3.00, 'other': 3.0000, 'time': 'wave2'},
            {'diab': 1.00, 'other': 0.0000, 'time': 'wave3'},
            {'diab': 12.0, 'other': 2.3000, 'time': 'wave4'}],
        'hiac': [
            {'diab': 10.2, 'other': 'ww', 'time': 'wave1'},
            {'diab': None, 'other': None, 'time': 'wave2'},
            {'diab': 2.30, 'other': 1.00, 'time': 'wave3'},
            {'diab': 21.2, 'other': 10.2, 'time': 'wave4'}],
        'hiad': [
            {'diab': 66.3, 'other': '10', 'time': 'wave1'},
            {'diab': None, 'other': None, 'time': 'wave2'},
            {'diab': 5.60, 'other': 0.00, 'time': 'wave3'},
            {'diab': 1.02, 'other': 66.3, 'time': 'wave4'}],
        'hiae': [
            {'diab': None, 'other': None, 'time': 'wave1'},
            {'diab': None, 'other': None, 'time': 'wave2'},
            {'diab': -12., 'other': 0.00, 'time': 'wave3'},
            {'diab': None, 'other': None, 'time': 'wave4'}],
        'gine': [
            {'diab': 3.40, 'other': 'cat2', 'time': 'wave1'},
            {'diab': 4.00, 'other': 4.0000, 'time': 'wave2'},
            {'diab': None, 'other': None, 'time': 'wave3'},
            {'diab': None, 'other': 3.4000, 'time': 'wave4'}]
    }
    assert r.shape.columnsDict == {'diab': Types.Numeric, 'other': Types.String, 'time': Types.Ordinal}


def test_validation():
    d = {'id': ['hiab', 'gine', 'hiac', 'hiaa', 'hiad'],
         'diab1': [2.3, 3.4, 10.2, 14.6, 66.3],
         'diab2': [3, 4, np.nan, 6, np.nan],
         'new1': ['cat1', 'cat2', 'ww', '1', '1']}
    e = {'id': ['hiab', 'hiae', 'hiac', 'hiaa', 'hiad'],
         'diab4': [12, np.nan, 21.2, 13.45, 1.02],
         'diab3': [1.0, -12, 2.3, 4.1, 5.6],
         'newt': [0, 0, 0, 0, 0]}
    f = data.Frame(d)
    g = data.Frame(e)
    f = f.setIndex('id')
    g = g.setIndex('id')
    w = WorkbenchModelMock()
    w.setDataframeByName('frameF', f)
    w.setDataframeByName('frameG', g)

    assert g.getRawFrame().index.name == 'id'
    assert f.getRawFrame().index.name == 'id'

    op = ExtractTimeSeries(w)

    timeLabels = ['wave1', 'wave2', 'wave3', 'wave4']

    options = {
        'diab': [('frameG', 0, 3), ('frameF', 1, 1), ('frameF', 0, 0), ('frameG', 1, 0)]
    }
    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(series=options, time=timeLabels, outName='frameR')
    assert e.value.invalid[0][0] == 'duplicates'

    options = {
        'diab': [('frameF', 1, 1), ('frameF', 0, 0), ('frameG', 1, 2)]
    }
    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(series=options, time=timeLabels, outName='frameR')
    assert e.value.invalid[0][0] == 'length'

    options = {
        'diab': [('frameG', 0, 3), ('frameF', 1, 1), ('frameF', 0, 0), ('frameG', 1, 2)]
    }
    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(series=options, time=timeLabels, outName='')
    assert e.value.invalid[0][0] == 'noname'

    options = {
        'diab': [('frameG', 0, 3), ('frameF', 1, 1), ('frameF', 0, 0), ('frameG', 1, 2)]
    }
    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(series=options, time=[], outName='gg')
    assert e.value.invalid[0][0] == 'notimelabels'

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(series=None, time=timeLabels, outName='gg')
    assert e.value.invalid[0][0] == 'noseries'

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(series={}, time=timeLabels, outName='gg')
    assert e.value.invalid[0][0] == 'noseries'
