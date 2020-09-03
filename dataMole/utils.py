from functools import wraps

import shiboken2
from PySide2.QtCore import QObject


def singleton(cls):
    """Make a class a Singleton class (only one instance)"""

    @wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton.instance

    wrapper_singleton.instance = None
    return wrapper_singleton


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
