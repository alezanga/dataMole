import abc

from data_preprocessor.data import Frame


class Saver(abc.ABC):
    @abc.abstractmethod
    def write(self, df: Frame, **kwargs) -> None:
        pass
