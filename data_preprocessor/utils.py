from data_preprocessor.decorators.generic import singleton


@singleton
class UIdGenerator:
    def __init__(self):
        self.__lastId: int = 0

    def getUniqueId(self) -> int:
        self.__lastId = self.__lastId + 1
        return self.__lastId
