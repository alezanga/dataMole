import pandas as pd
import pytest

from data_preprocessor.data import Frame
from data_preprocessor.data.types import Types
from data_preprocessor.operation.dateoperations import DateDiscretizer
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from tests.utilities import nan_to_None


def test_discretize_by_date():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']
         }

    f = Frame(d)

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] is Types.String

    intervals = [(pd.Interval(pd.Timestamp('01-01-1950'), pd.Timestamp('01-01-1970')), '50'),
                 (pd.Interval(pd.Timestamp('01-01-1970'), pd.Timestamp('01-01-1990')), '70'),
                 (pd.Interval(pd.Timestamp('30-12-1994'), pd.Timestamp('01-01-2010')), 'skip'),
                 (pd.Interval(pd.Timestamp('01-01-2010'), pd.Timestamp('01-01-2030')), 'now')]

    op.setOptions(attribute=2, intervals=intervals, byDate=True, byTime=False)
    shapeDict['cold'] = Types.Ordinal
    assert op.getOutputShape().columnsDict == shapeDict

    g = op.execute(f)
    assert g.shape.columnsDict == shapeDict

    output = nan_to_None(g.to_dict())
    assert output == {'col2': [3, 4, 5.1, 6, 0],
                      'col3': ['123', '2', '0.43', '4', '2021 January'],
                      'cold': ['70', None, 'skip', None, 'now']
                      }
    assert g.getRawFrame().iloc[:, 2].cat.categories.to_list() == ['50', '70', 'skip', 'now']
    assert g.getRawFrame().iloc[:, 2].dtype.ordered is True


def test_discretize_by_date_with_None():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': [pd.Timestamp('05-09-1988'), pd.Timestamp('22-12-1994'),
                  pd.Timestamp('21-11-1995'), None, pd.Timestamp('12-12-2012')]
         }

    f = Frame(d)

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] == Types.Datetime

    intervals = [(pd.Interval(pd.Timestamp('01-01-1950'), pd.Timestamp('01-01-1970')), '50'),
                 (pd.Interval(pd.Timestamp('01-01-1970'), pd.Timestamp('01-01-1990')), '70'),
                 (pd.Interval(pd.Timestamp('30-12-1994'), pd.Timestamp('01-01-2010')), 'skip'),
                 (pd.Interval(pd.Timestamp('01-01-2010'), pd.Timestamp('01-01-2030')), 'now')]

    op.setOptions(attribute=2, intervals=intervals, byDate=True, byTime=False)
    shapeDict['cold'] = Types.Ordinal
    assert op.getOutputShape().columnsDict == shapeDict

    g = op.execute(f)
    assert g.shape.columnsDict == shapeDict
    assert g.shape.indexDict == f.shape.indexDict

    output = nan_to_None(g.to_dict())
    assert output == {'col2': [3, 4, 5.1, 6, 0],
                      'col3': ['123', '2', '0.43', '4', '2021 January'],
                      'cold': ['70', None, 'skip', None, 'now']
                      }
    assert g.getRawFrame().iloc[:, 2].cat.categories.to_list() == ['50', '70', 'skip', 'now']
    assert g.getRawFrame().iloc[:, 2].dtype.ordered is True


def test_discretize_by_date_and_time():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': [pd.Timestamp('05-09-1988 13:45'), pd.Timestamp('22-12-1994 14:21'),
                  pd.Timestamp('21-11-1995 11:50'), None, pd.Timestamp('12-12-2012 09:15')]
         }

    f = Frame(d)

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] == Types.Datetime

    intervals = [
        (pd.Interval(pd.Timestamp('20-12-1994 11:30'), pd.Timestamp('05-09-2000 14:20')), 'middle'),
        (pd.Interval(pd.Timestamp('05-09-1988 07:00'), pd.Timestamp('05-09-1994 11:30')), 'early'),
        (pd.Interval(pd.Timestamp('01-09-2010 14:30'), pd.Timestamp('12-12-2012 09:14')), 'late')]

    op.setOptions(attribute=2, intervals=intervals, byDate=True, byTime=True)
    shapeDict['cold'] = Types.Ordinal
    assert op.getOutputShape().columnsDict == shapeDict

    g = op.execute(f)
    assert g.shape.columnsDict == shapeDict
    assert g.shape.indexDict == f.shape.indexDict

    output = nan_to_None(g.to_dict())
    assert output == {'col2': [3, 4, 5.1, 6, 0],
                      'col3': ['123', '2', '0.43', '4', '2021 January'],
                      'cold': ['early', 'middle', 'middle', None, None]
                      }
    assert g.getRawFrame().iloc[:, 2].cat.categories.to_list() == ['middle', 'early', 'late']
    assert g.getRawFrame().iloc[:, 2].dtype.ordered is True


def test_discretize_set_options_exceptions():
    d = {'col2': [3, 4, 5.1, 6, 0],
         'col3': ['123', '2', '0.43', '4', '2021 January'],
         'cold': [pd.Timestamp('05-09-1988 13:45'), pd.Timestamp('22-12-1994 14:21'),
                  pd.Timestamp('21-11-1995 11:50'), None, pd.Timestamp('12-12-2012 09:15')]
         }

    f = Frame(d)

    op = DateDiscretizer()
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)
    assert op.getOutputShape() is None
    shapeDict = f.shape.columnsDict
    assert shapeDict['cold'] == Types.Datetime

    intervals = [
        (pd.Interval(pd.Timestamp('05-09-1988 07:00'), pd.Timestamp('05-09-1994 11:30')), 'early'),
        (pd.Interval(pd.Timestamp('01-01-1994 11:30'), pd.Timestamp('05-09-2000 14:20')), 'middle'),
        (pd.Interval(pd.Timestamp('01-09-2010 14:30'), pd.Timestamp('12-12-2012 09:14')), 'late')]

    with pytest.raises(OptionValidationError):
        op.setOptions(attribute=2, intervals=intervals, byDate=True, byTime=True)

    with pytest.raises(OptionValidationError):
        op.setOptions(attribute=None, intervals=intervals, byDate=True, byTime=False)

    intervals = [
        (pd.Interval(pd.Timestamp('05-09-1988 07:00'), pd.Timestamp('05-09-1994 11:30')), 'early'),
        (pd.Interval(pd.Timestamp('01-01-1994 11:30'), pd.Timestamp('05-09-2000 14:20')), 'middle'),
        (pd.Interval(pd.Timestamp('01-09-2010 14:30'), pd.Timestamp('12-12-2012 09:14')), '')]

    with pytest.raises(OptionValidationError):
        op.setOptions(attribute=2, intervals=intervals, byDate=True, byTime=False)

    assert op.getOutputShape() is None
