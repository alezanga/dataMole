# Tests for generic GraphOperation
import pytest

from data_preprocessor.data import Frame
from .DummyOp import DummyOp


def test_addInputShape_exc():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    f = Frame(d)
    op = DummyOp()
    with pytest.raises(ValueError):
        op.addInputShape(f.shape, pos=-1)


def test_add_removeInputShape():
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', '2', 'c', '4', 'x'],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}

    f = Frame(d)

    class MyOp(DummyOp):
        def maxInputNumber(self) -> int:
            return 2

    mop = MyOp()

    gs = f.shape
    gs.col_names[0] = 'hola'

    mop.addInputShape(f.shape, pos=1)
    mop.addInputShape(gs, pos=0)

    assert mop._shapes == [gs, f.shape]
    assert mop._shapes != [f.shape, gs]

    # Test if exception is thrown
    with pytest.raises(IndexError):
        mop.addInputShape(gs, pos=2)

    # Test if exception is thrown in DummyOp
    with pytest.raises(IndexError):
        DummyOp().addInputShape(gs, pos=1)

    # Adding / removing input shape should preserve the list length
    ss = mop._shapes.copy()
    mop.removeInputShape(pos=0)
    assert mop._shapes == [None, ss[1]]

    mop.addInputShape(gs, pos=0)
    assert mop._shapes == [gs, f.shape]


def test_hasAttributeShape():
    b = DummyOp()
    assert hasattr(b, '_shapes')
    assert isinstance(b._shapes, list)

    del b._shapes
    assert not hasattr(b, '_shapes')
