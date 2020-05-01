from typing import Callable

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QFrame, QWidget


class FramedPanel(QFrame):
    def __init__(self, parent: QWidget = None, flags: Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, flags)

        # Setup style
        self.setContentsMargins(15, 15, 15, 15)
        # self.setFrameShape(QFrame.StyledPanel)
        # self.setFrameShadow(QFrame.Plain)
        # self.setFrameStyle(QFrame.Panel)
        self.setStyleSheet('QFrame { border: 1px solid black; border-radius: 10px; padding: 10px; '
                           'margin: 10px; }')


def frameDecorator(fun: Callable[..., QWidget]) -> Callable[..., QWidget]:
    """ Adds a framed panel around a QWidget """
    def wrapper_frame_decorator(*args, **kwargs):
        parent_kw: QWidget = kwargs['parent'] if 'parent' in kwargs else None
        parent_ar: QWidget = args[0] if len(args) > 0 else None
        if parent_kw:
            f = FramedPanel(parent_kw)
        elif parent_ar:
            f = FramedPanel(parent_ar)
        else:
            f = FramedPanel()
        widget: QWidget = fun(*args, **kwargs)
        widget.setParent(f)
        return f

    return wrapper_frame_decorator
