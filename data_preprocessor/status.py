import enum


@enum.unique
class NodeStatus(enum.Enum):
    NONE = 0
    SUCCESS = 1
    ERROR = 2
    PROGRESS = 3