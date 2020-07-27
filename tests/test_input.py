from data_preprocessor.data import Frame, Shape
from data_preprocessor.operation.input import SetInput
from tests.mocks import WorkbenchModelMock


def test_SetInput():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    f = Frame(d)

    work = WorkbenchModelMock()
    # Set dataframe
    work.setDataframeByName('var', f)

    op = SetInput(work)
    assert op.getOutputShape() is None
    assert op.getOptions() == {'inputF': None}
    op.setOptions(inputF='var')
    op.addInputShape(Shape(), pos=0)  # this does nothing
    assert op.getOptions() == {'inputF': 'var'}

    assert op.getOutputShape() == f.shape

    g = op.execute()
    assert g == f

    # g should be a copy
    f = f.rename({'col1': 'ewew'})
    assert g != f
