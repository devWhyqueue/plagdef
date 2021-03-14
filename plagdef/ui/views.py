import sys

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtGui import QCursor, QMovie
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QButtonGroup, QMainWindow


class MainWindowFactory:
    @classmethod
    def create(cls) -> QMainWindow:
        window = cls._load_ui_file()
        cls._init_widgets(window)
        return window

    @classmethod
    def _load_ui_file(cls) -> QMainWindow:
        ui_file_name = "ui/main.ui"
        main_ui = QFile(ui_file_name)
        if not main_ui.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_name}: {main_ui.errorString()}")
            sys.exit(-1)
        loader = QUiLoader()
        window = loader.load(main_ui)
        main_ui.close()
        if not window:
            print(loader.errorString())
            sys.exit(-1)
        return window

    @classmethod
    def _init_widgets(cls, window: QMainWindow):
        window.open_folder_button.setCursor(QCursor(Qt.PointingHandCursor))
        window.radio_buttons = QButtonGroup()
        window.radio_buttons.addButton(window.eng_radio)
        window.radio_buttons.addButton(window.ger_radio)
        window.detect_button.setCursor(QCursor(Qt.PointingHandCursor))
        window.folder_name_label.setVisible(False)
        window.remove_folder_button.setCursor(QCursor(Qt.PointingHandCursor))
        window.remove_folder_button.setVisible(False)
        window.sel_lang_label.setVisible(False)
        window.change_lang_button.setCursor(QCursor(Qt.PointingHandCursor))
        window.change_lang_button.setVisible(False)
        movie = QMovie(':/res/loading.gif')
        window.loading_movie_label.setMovie(movie)
        window.again_button.setCursor(QCursor(Qt.PointingHandCursor))
        window.again_button_err.setCursor(QCursor(Qt.PointingHandCursor))
        window.again_button_res.setCursor(QCursor(Qt.PointingHandCursor))
        window.xml_button.setCursor(QCursor(Qt.PointingHandCursor))
        movie.start()  # TODO: Move
