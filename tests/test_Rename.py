from data_preprocessor.data import Frame
from data_preprocessor.operation.rename import RenameOp


def test_rename():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = RenameOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(names={0: 'col4', 2: 'col1'})

    os = f.shape.clone()
    os.colNames = ['col4', 'col2', 'col1']

    assert op.getOutputShape() == os

    g = op.execute(f)
    gd = {'col4': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col1': ['q', '2', 'c', '4', 'x']}
    assert g.to_dict() == gd


def test_unsetOptions():
    d = {'col1': [1, 2, 3, 4, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x']}
    f = Frame(d)

    op = RenameOp()
    op.addInputShape(f.shape, pos=0)
    op.setOptions(names={0: 'col4', 2: 'col1'})

    assert op.getOptions() == [{0: 'col4', 2: 'col1'}]

    op.unsetOptions()

    assert op.getOptions() == [{}]
