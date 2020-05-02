from data_preprocessor.data import Frame, Shape
from data_preprocessor.data.Workbench import Workbench
from data_preprocessor.operation.CopyOp import CopyOp


def test_copy():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    f = Frame(d)

    work = Workbench()
    work['var'] = f

    op = CopyOp(work)
    op.setOptions('var')
    op.inferInputShape()
    op.addInputShape(Shape(), pos=0)  # this does nothing

    assert op._shape[0] == op.getOutputShape() == f.shape

    g = op.execute()
    assert g == f

    # g should be a copy
    f = f.rename({'col1': 'ewew'})
    assert g != f
