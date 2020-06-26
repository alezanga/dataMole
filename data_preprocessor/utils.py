import shiboken2
from PySide2.QtCore import QObject

from data_preprocessor.decorators.generic import singleton


@singleton
class UIdGenerator:
    def __init__(self):
        self.__lastId: int = 0

    def getUniqueId(self) -> int:
        self.__lastId = self.__lastId + 1
        return self.__lastId


def safeDelete(obj: QObject) -> None:
    """ Calls deleteLater() on a QObject, doing nothing if the object was already deleted """
    if obj and shiboken2.isValid(obj):
        obj.deleteLater()
