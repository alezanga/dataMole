from typing import List, Dict

from dataMole import data


class FrameModelMock:
    def __init__(self, frame: data.Frame, name: str):
        self.__frame: data.Frame = frame
        self.name = name

    def setFrame(self, frame: data.Frame) -> None:
        self.__frame = frame

    @property
    def frame(self) -> data.Frame:
        return self.__frame

    @property
    def shape(self) -> data.Shape:
        return self.__frame.shape


class WorkbenchModelMock:
    def __init__(self):
        self.__workbench: List[FrameModelMock] = list()
        self.__nameToIndex: Dict[str, int] = dict()

    @property
    def modelList(self) -> List[FrameModelMock]:
        return self.__workbench

    @property
    def modelDict(self) -> Dict[str, FrameModelMock]:
        return {n: self.__workbench[i] for n, i in self.__nameToIndex.items()}

    @property
    def names(self) -> List[str]:
        return list(self.__nameToIndex.keys())

    def rowCount(self) -> int:
        return len(self.__workbench)

    def getDataframeModelByIndex(self, index: int) -> FrameModelMock:
        return self.__workbench[index]

    def getDataframeModelByName(self, name: str) -> FrameModelMock:
        return self.__workbench[self.__nameToIndex[name]]

    def setDataframeByName(self, name: str, value: data.Frame) -> bool:
        listPos: int = self.__nameToIndex.get(name, None)
        if listPos is not None:
            # Name already exists
            if self.__workbench[listPos].frame is value:
                return False
            frame_model = self.getDataframeModelByIndex(listPos)
            # This will reset any view currently showing the frame
            frame_model.setFrame(value)
            self.__workbench[listPos] = frame_model
            # nameToIndex is already updated (no change)
            # dataChanged is not emitted because the frame name has not changed
        else:
            # Name does not exists
            row = self.rowCount()
            f = FrameModelMock(value, name)
            self.__workbench.append(f)
            self.__nameToIndex[name] = row
        return True

    def removeRow(self, row: int) -> bool:
        if not 0 <= row < self.rowCount():
            return False
        # Update views showing the frame
        frame_model = self.getDataframeModelByIndex(row)
        # Reset connected models by showing an empty frame. This also delete their reference
        frame_model.setFrame(frame=data.Frame())
        # Now delete row
        rowName: str = self.__workbench[row].name
        del self.__workbench[row]
        self.__nameToIndex = {name: (i if i < row else i - 1)
                              for name, i in self.__nameToIndex.items() if i != row}
        return True

    def appendEmptyRow(self) -> bool:
        row = self.rowCount()
        # Create a dummy entry
        f = FrameModelMock(data.Frame(), ' ')
        self.__workbench.append(f)
        self.__nameToIndex[f.name] = row
        return True
