from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.operation.onehotencoder import OneHotEncodeOp


def test_ohe():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', 2, 'q', 'q', 2],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)

    op = OneHotEncodeOp()
    op.setOptions(attributes=[2], includeNan=True)

    op.addInputShape(f.shape, 0)
    s = f.shape.copy()
    del s.col_names[2]
    del s.col_types[2]
    s = s.col_type_dict
    s['col3_2'] = Types.Categorical
    s['col3_nan'] = Types.Categorical
    s['col3_q'] = Types.Categorical
    assert op.getOutputShape() is None

    g = op.execute(f)

    assert g != f and g.shape.col_type_dict == s
