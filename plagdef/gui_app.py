import sys

from PySide6.QtWidgets import QApplication

# noinspection PyUnresolvedReferences
import plagdef.gui.resources
from plagdef.gui.controllers import MainWindowController

if __name__ == "__main__":
    app = QApplication()
    main_window = MainWindowController.create()
    main_window.show()
    sys.exit(app.exec_())
