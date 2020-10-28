from dataMole import data
from dataMole.data.types import Types
from dataMole.operation.onehotencoder import OneHotEncoder


def test_ohe():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': ['3', '4', '5', '6', '0'], 'col3': ['q', 2, 'q', 'q', 2],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012'],
         'col3_q': [0, 1, 2, 2, 2]}
    f = data.Frame(d)
    f = f.setIndex(['col1', 'date'])

    op = OneHotEncoder()
    opts = {1: None, 0: None}
    op.setOptions(attributes=opts, includeNan=True)
    opts[2] = [1, 2, 3]

    assert op.getOptions() == {
        'attributes': {0: None, 1: None},
        'includeNan': True
    }

    op.addInputShape(f.shape, 0)
    s = f.shape.clone()
    cd = s.columnsDict
    cd['col3_2'] = Types.Nominal
    cd['col3_nan'] = Types.Nominal
    cd['col3_q'] = Types.Nominal

    cd['col2_0'] = Types.Nominal
    cd['col2_3'] = Types.Nominal
    cd['col2_4'] = Types.Nominal
    cd['col2_5'] = Types.Nominal
    cd['col2_6'] = Types.Nominal
    cd['col2_nan'] = Types.Nominal
    s = data.Shape.fromDict(cd, s.indexDict)
    assert op.getOutputShape() is None

    g = op.execute(f)

    assert g != f and g.shape == s
