from data_preprocessor.decorators.generic import singleton


@singleton
class OperationUidFactory:
    def __init__(self):
        self.__lastId: int = 0

    def getUniqueId(self) -> 'OperationUid':
        self.__lastId = self.__lastId + 1
        return OperationUid(self.__lastId)


class OperationUid:
    def __init__(self, id: int):
        self.uid: int = id
