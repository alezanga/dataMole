from data_preprocessor.data import Frame
from data_preprocessor.data.Workbench import Workbench


def test_workbench():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    f = Frame(d)

    work = Workbench()
    work['var'] = f
    work['new'] = f

    assert len(work) == 2

    del work['var']

    assert len(work) == 1

    work['ab'] = Frame()

    l = list()
    for k in work.keys():
        l.append(k)

    assert l == ['new', 'ab']
