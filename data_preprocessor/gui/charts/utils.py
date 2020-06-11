import math
from typing import List

from PySide2.QtGui import QColor


def randomColors(count: int) -> List[QColor]:
    colors = list()
    current: float = 0.0
    for i in range(0, count):
        colors.append(QColor.fromHslF(current, 1.0, 0.5))
        current += 0.618033988749895
        current = math.fmod(current, 1.0)
    return colors
