import numpy as np
import pandas as pd
import pytest

from data_preprocessor import data, exceptions as exc
from data_preprocessor.data.types import Types, IndexType
from data_preprocessor.operation.dropcols import Drop
from tests.utilities import nan_to_None


def test_drop_columns():
    e = {'col1': [np.nan, 2, np.nan, 4, 10],
         'col2': pd.Categorical(['3', '4', np.nan, np.nan, '0'], ordered=True),
         'col3': ['q', '2', 'c', np.nan, np.nan],
         'date': pd.Series(['05-09-1988', np.nan, np.nan, '22-06-1994', '12-12-2012'],
                           dtype='datetime64[ns]')}
    g = data.Frame(e)

    g = g.setIndex('col1')

    op = Drop()
    assert op.getOutputShape() is None
    op.addInputShape(g.shape, 0)
    assert op.getOutputShape() is None
    assert op.getOptions() == {
        'selected': dict()
    }

    selOpts = {0: None, 2: None}
    op.setOptions(selected={0: None, 2: None})
    opts = op.getOptions()
    assert opts['selected'] == selOpts
    opts['selected'] = {}
    assert op.getOptions()['selected'] == selOpts
    assert op.getOptions() != opts

    with pytest.raises(exc.OptionValidationError) as e:
        op.setOptions(selected={})

    s = data.Shape()
    s.colNames = ['col3']
    s.colTypes = [Types.String]
    s.index = ['col1']
    s.indexTypes = [IndexType(Types.Numeric)]
    assert op.getOutputShape() == s

    h = op.execute(g)
    assert h.shape == s

    assert nan_to_None(h.to_dict()) == {
        'col3': ['q', '2', 'c', None, None]
    }
