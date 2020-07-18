from typing import List

import pandas as pd
import pytest
from PySide2.QtCore import QDateTime

from data_preprocessor import data, exceptions as exp
from data_preprocessor.data.types import Types
from data_preprocessor.operation.dateoperations import DateDiscretizer, _IntervalWidget, toQtDateTime
from tests.utilities import nan_to_None


def test_discretize_by_date():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']
         }

    f = data.Frame(d)

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] is Types.String

    intervals = [pd.Timestamp('01-01-1950'),
                 pd.Timestamp('01-01-1970'),
                 pd.Timestamp('30-12-1994'),
                 pd.Timestamp('01-01-2010')]

    op.setOptions(selected={2: {'ranges': (intervals, True, False), 'labels': ['50', '70', 'now']}},
                  suffix=(False, None))
    assert op.getOptions() == {'selected':
                                   {2: {'ranges': (intervals, True, False),
                                        'labels': ['50', '70', 'now']}},
                               'suffix': (False, None)
                               }
    shapeDict['cold'] = Types.Ordinal
    s = data.Shape.fromDict(shapeDict, f.shape.indexDict)

    assert op.getOutputShape() == s

    g = op.execute(f)
    assert g.shape == s

    output = nan_to_None(g.to_dict())
    assert output == {'col2': [3, 4, 5.1, 6, 0],
                      'col3': ['123', '2', '0.43', '4', '2021 January'],
                      'cold': ['70', '70', 'now', '70', None]
                      }
    assert g.getRawFrame().iloc[:, 2].cat.categories.to_list() == ['50', '70', 'now']
    assert g.getRawFrame().iloc[:, 2].dtype.ordered is True


def test_discretize_by_date_with_None():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': [pd.Timestamp('05-09-1988'), pd.Timestamp('22-12-1994'),
                  pd.Timestamp('21-11-1995'), None, pd.Timestamp('12-12-2012')],
         'cold2': [pd.Timestamp('01-01-1950'), pd.Timestamp('22-12-1980'),
                   pd.Timestamp('21-11-1995'), None, pd.Timestamp('12-12-2034')],
         'cold_disc': [None, None, None, None, None]  # test to see if it is removed
         }

    f = data.Frame(d)
    f = f.setIndex('col2')

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] == Types.Datetime
    assert shapeDict['cold2'] == Types.Datetime

    intervals = [pd.Timestamp('01-01-1950'), pd.Timestamp('01-01-1970'),
                 pd.Timestamp('01-01-1990'), pd.Timestamp('01-01-2010'),
                 pd.Timestamp('01-01-2030')]

    op.setOptions(selected={
        1: {'ranges': (intervals, True, False), 'labels': ['50', '70', '80', 'now']},
        2: {'ranges': (intervals, True, True), 'labels': ['50', '70', '80', 'now']}},
        suffix=(True, '_disc'))

    assert op.getOptions() == {
        'selected': {
            1: {'ranges': (intervals, True, False), 'labels': ['50', '70', '80', 'now']},
            2: {'ranges': (intervals, True, True), 'labels': ['50', '70', '80', 'now']}},
        'suffix': (True, '_disc')
    }

    shapeDict['cold_disc'] = Types.Ordinal
    shapeDict['cold2_disc'] = Types.Ordinal
    s = data.Shape.fromDict(shapeDict, f.shape.indexDict)
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert g.shape == s

    output = nan_to_None(g.to_dict())
    assert output == {'col3': ['123', '2', '0.43', '4', '2021 January'],
                      'cold': [pd.Timestamp('05-09-1988'), pd.Timestamp('22-12-1994'),
                               pd.Timestamp('21-11-1995'), None, pd.Timestamp('12-12-2012')],
                      'cold2': [pd.Timestamp('01-01-1950'), pd.Timestamp('22-12-1980'),
                                pd.Timestamp('21-11-1995'), None, pd.Timestamp('12-12-2034')],
                      'cold_disc': ['70', '80', '80', None, 'now'],
                      'cold2_disc': [None, '70', '80', None, None]
                      }
    assert g.getRawFrame()['cold_disc'].cat.categories.to_list() == ['50', '70', '80', 'now']
    assert g.getRawFrame()['cold_disc'].dtype.ordered is True
    assert g.getRawFrame()['cold2_disc'].cat.categories.to_list() == ['50', '70', '80', 'now']
    assert g.getRawFrame()['cold2_disc'].dtype.ordered is True


def test_discretize_by_date_and_time():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': [pd.Timestamp('05-09-1988 13:45'), pd.Timestamp('22-12-1994 14:21'),
                  pd.Timestamp('21-11-1995 11:50'), None, pd.Timestamp('12-12-2012 09:15')],
         'cold2': [pd.Timestamp('05-09-1988 13:45'), pd.Timestamp('22-12-1994 14:21'),
                   pd.Timestamp('21-11-1995 11:50'), None, pd.Timestamp('12-12-2012 09:15')]
         }

    f = data.Frame(d)
    f = f.setIndex(['col2', 'col3'])

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] == Types.Datetime

    intervals = [pd.Timestamp('05-09-1988 07:00'), pd.Timestamp('20-12-1994 11:30'),
                 pd.Timestamp('05-09-2000 14:20'), pd.Timestamp('01-09-2010 14:30'),
                 pd.Timestamp('12-12-2012 09:14')]
    labels = ['early', 'middle', 'late', 'now']

    op.setOptions(selected={
        0: {'ranges': (intervals, True, True), 'labels': labels},
        1: {'ranges': (intervals, True, True), 'labels': labels}},
        suffix=(False, '_disc'))

    assert op.getOptions() == {
        'selected': {
            0: {'ranges': (intervals, True, True), 'labels': labels},
            1: {'ranges': (intervals, True, True), 'labels': labels}},
        'suffix': (False, None)
    }

    shapeDict['cold'] = Types.Ordinal
    shapeDict['cold2'] = Types.Ordinal
    s = data.Shape.fromDict(shapeDict, f.shape.indexDict)
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert g.shape == s
    assert g.shape != f.shape

    output = nan_to_None(g.to_dict())
    assert output == {
        'cold': ['early', 'middle', 'middle', None, None],
        'cold2': ['early', 'middle', 'middle', None, None]}
    assert g.getRawFrame()['cold'].cat.categories.to_list() == ['early', 'middle', 'late', 'now']
    assert g.getRawFrame()['cold'].dtype.ordered is True
    assert g.getRawFrame()['cold2'].cat.categories.to_list() == ['early', 'middle', 'late', 'now']
    assert g.getRawFrame()['cold2'].dtype.ordered is True


def withDefaultDate(ll: List[pd.Timestamp]) -> List[pd.Timestamp]:
    date = _IntervalWidget.DEFAULT_DATE
    nl = [pd.Timestamp(QDateTime(date, toQtDateTime(ts.to_pydatetime()).time()).toPython()) for ts in ll]
    return nl


def test_discretize_by_time():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': [pd.Timestamp('10:42'), pd.Timestamp('23:59:07'),
                  pd.Timestamp('07:12'), None, pd.Timestamp('18:13')],
         'cold2': [pd.Timestamp('22:59'), pd.Timestamp('12:00'),
                   pd.Timestamp('16:40:02'), pd.Timestamp('16:40:03'), pd.Timestamp('22:00:02')],
         'nan': [None, None, None, None, None],
         'cold_disc': [None, None, None, None, None]  # test to see if it is removed
         }

    f = data.Frame(d)
    f = f.setIndex(['col2', 'col3'])

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] == Types.Datetime
    assert shapeDict['cold2'] == Types.Datetime

    intervals = [pd.Timestamp('00:00'), pd.Timestamp('06:00'), pd.Timestamp('12:00'),
                 pd.Timestamp('16:40:02'), pd.Timestamp('22:00'),
                 pd.Timestamp('23:59')]
    labels = ['night1', 'morning', 'afternoon', 'evening', 'night2']

    # It's necessary to set a default date object, which is normally done by the editor
    intervals = withDefaultDate(intervals)
    op.setOptions(selected={
        0: {'ranges': (intervals, False, True), 'labels': labels},
        1: {'ranges': (intervals, False, True), 'labels': labels},
        2: {'ranges': (intervals, False, True), 'labels': labels}},
        suffix=(True, '_disc'))

    assert op.getOptions() == {
        'selected': {
            0: {'ranges': (intervals, False, True), 'labels': labels},
            1: {'ranges': (intervals, False, True), 'labels': labels},
            2: {'ranges': (intervals, False, True), 'labels': labels}},
        'suffix': (True, '_disc')
    }

    shapeDict['cold_disc'] = Types.Ordinal
    shapeDict['cold2_disc'] = Types.Ordinal
    shapeDict['nan_disc'] = Types.Ordinal
    s = data.Shape.fromDict(shapeDict, f.shape.indexDict)
    assert op.getOutputShape() == s

    g = op.execute(f)
    assert g.shape == s

    output = nan_to_None(g.to_dict())
    assert output == {'cold': [pd.Timestamp('10:42'), pd.Timestamp('23:59:07'),
                               pd.Timestamp('07:12'), None, pd.Timestamp('18:13')],
                      'cold2': [pd.Timestamp('22:59'), pd.Timestamp('12:00'),
                                pd.Timestamp('16:40:02'), pd.Timestamp('16:40:03'),
                                pd.Timestamp('22:00:02')],
                      'nan': [None, None, None, None, None],
                      'nan_disc': [None, None, None, None, None],
                      'cold_disc': ['morning', None, 'morning', None, 'evening'],
                      'cold2_disc': ['night2', 'morning', 'afternoon', 'evening', 'night2']
                      }
    assert g.getRawFrame()['cold_disc'].cat.categories.to_list() == labels
    assert g.getRawFrame()['cold_disc'].dtype.ordered is True
    assert g.getRawFrame()['cold2_disc'].cat.categories.to_list() == labels
    assert g.getRawFrame()['cold2_disc'].dtype.ordered is True
    assert g.getRawFrame()['nan_disc'].cat.categories.to_list() == labels
    assert g.getRawFrame()['nan_disc'].dtype.ordered is True


def test_discretize_set_options_exceptions():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': [pd.Timestamp('05-09-1988 13:45'), pd.Timestamp('22-12-1994 14:21'),
                  pd.Timestamp('21-11-1995 11:50'), None, pd.Timestamp('12-12-2012 09:15')]
         }

    f = data.Frame(d)

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] == Types.Datetime

    intervals = [pd.Timestamp('05-09-1988 07:00'), pd.Timestamp('20-12-1994 11:30'),
                 pd.Timestamp('05-09-2000 14:20'), pd.Timestamp('01-09-2010 14:30'),
                 pd.Timestamp('12-12-2012 09:14')]
    labels = ['early', 'middle', 'late', 'now']

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(selected={
            2: {'ranges': (list(), True, True), 'labels': labels}},
            suffix=(False, '_disc'))
    assert e.value.invalid[0][0] == 'bins'

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(selected={
            2: {'ranges': None, 'labels': labels}},
            suffix=(False, '_disc'))
    assert e.value.invalid[0][0] == 'bins'

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(selected={
            2: {'ranges': (intervals, False, True), 'labels': labels[:1]}},
            suffix=(False, '_disc'))
    assert e.value.invalid[0][0] == 'len'

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(selected={
            2: {'ranges': (intervals, False, True), 'labels': None}},
            suffix=(False, '_disc'))
    assert e.value.invalid[0][0] == 'lab'

    with pytest.raises(exp.OptionValidationError) as e:
        op.setOptions(selected={
            2: {'ranges': (intervals, False, True), 'labels': labels}},
            suffix=(True, ''))
    assert e.value.invalid[0][0] == 'suff'

    assert op.getOutputShape() is None
