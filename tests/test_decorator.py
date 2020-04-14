import abc
import pytest
from data_preprocessor.decorators.generic import *


class A(abc.ABC):
    @abc.abstractmethod
    def fun(self):
        pass


class B:
    def hola(self):
        return 2


def test_abs():
    with pytest.raises(TypeError):
        class C(A):
            def fun1(self):
                pass

        a = C()


def test_decorator():
    @add_method(B)
    def fun():
        return -1

    g = B()

    assert g.fun() == -1 and not issubclass(B, A)
