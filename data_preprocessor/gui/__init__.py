from . import window
from .notifications import Notifier
from .statusbar import StatusBar

# Access variable for singleton GUI objects
statusBar: StatusBar = None
notifier: Notifier = None
