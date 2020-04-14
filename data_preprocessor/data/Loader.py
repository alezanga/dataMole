import abc
from data_preprocessor.data import Frame


class Loader(abc.ABC):
    @abc.abstractmethod
    def read(self, **kwargs) -> Frame:
        pass
