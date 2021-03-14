
import sys

from PySide6.QtWidgets import QApplication

# noinspection PyUnresolvedReferences
import ui.resources
from plagdef.ui.controller import MainWindowController

if __name__ == "__main__":
    app = QApplication()
    main_window_controller = MainWindowController()
    main_window_controller.show()
    sys.exit(app.exec_())
