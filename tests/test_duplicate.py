from copy import deepcopy

from data_preprocessor import data
from data_preprocessor.operation.duplicate import DuplicateColumn


def test_duplicate_columns():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', 2, 'q', 'q', 2],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    f = data.Frame(d)
    f.setIndex('col1')

    op = DuplicateColumn()
    assert op.getOutputShape() is None
    opt = {'table': {0: {'rename': 'a name'}, 2: {'rename': 'new'}}}
    op.setOptions(**opt)
    assert op.getOutputShape() is None
    op.addInputShape(f.shape, 0)

    assert op.getOptions() == opt
    copt = deepcopy(opt)
    opt['table'][0]['rename'] = 'newnn'
    assert op.getOptions() == copt and op.getOptions() != opt

    s = f.shape.clone()
    s.colNames.append('a name')
    s.colNames.append('new')
    s.colTypes.append(s.colTypes[0])
    s.colTypes.append(s.colTypes[2])
    assert op.getOutputShape() == s

    g = op.execute(f)

    assert g != f and g.shape == s
