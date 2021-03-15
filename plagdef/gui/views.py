import sys
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtGui import QCursor, QMovie
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QButtonGroup, QMainWindow, QWidget

from plagdef.gui.model import ResultsTableModel, DocumentPairMatch, Config


class MainWindow:
    @classmethod
    def create(cls, configure_widget: QWidget, loading_widget: QWidget, error_widget: QWidget,
               no_res_widget: QWidget, res_widget: QWidget) -> QMainWindow:
        cls._window = _load_ui_file(Path('gui/ui/main_window.ui'))
        cls._configure(configure_widget, loading_widget, no_res_widget, error_widget, res_widget)
        return cls._window

    @classmethod
    def _configure(cls, configure_widget, loading_widget, no_res_widget, error_widget, res_widget):
        cls._window.stacked_widget.addWidget(configure_widget)
        cls._window.stacked_widget.addWidget(loading_widget)
        cls._window.stacked_widget.addWidget(error_widget)
        cls._window.stacked_widget.addWidget(no_res_widget)
        cls._window.stacked_widget.addWidget(res_widget)


class ConfigureWidget:
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = _load_ui_file(Path('gui/ui/configure_widget.ui'))
        cls._configure()
        return cls._widget

    @classmethod
    def _configure(cls):
        cls.config = Config(None, None)
        cls._widget.open_folder_button.setCursor(QCursor(Qt.PointingHandCursor))
        cls._widget.radio_buttons = QButtonGroup()
        cls._widget.radio_buttons.addButton(cls._widget.eng_radio)
        cls._widget.radio_buttons.addButton(cls._widget.ger_radio)
        cls._widget.detect_button.setCursor(QCursor(Qt.PointingHandCursor))
        cls._widget.folder_name_label.setVisible(False)
        cls._widget.remove_folder_button.setCursor(QCursor(Qt.PointingHandCursor))
        cls._widget.remove_folder_button.setVisible(False)
        cls._widget.sel_lang_label.setVisible(False)
        cls._widget.change_lang_button.setCursor(QCursor(Qt.PointingHandCursor))
        cls._widget.change_lang_button.setVisible(False)


class LoadingWidget:
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = _load_ui_file(Path('gui/ui/loading_widget.ui'))
        cls._configure()
        return cls._widget

    @classmethod
    def _configure(cls):
        cls._movie = QMovie(':/loading.gif')
        cls._widget.loading_movie_label.setMovie(cls._movie)

    @classmethod
    def start_movie(cls):
        cls._movie.start()

    @classmethod
    def stop_movie(cls):
        cls._movie.stop()


class NoResultsWidget:
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = _load_ui_file(Path('gui/ui/no_results_widget.ui'))
        cls._configure()
        return cls._widget

    @classmethod
    def _configure(cls):
        cls._widget.again_button_no_res.setCursor(QCursor(Qt.PointingHandCursor))


class ErrorWidget:
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = _load_ui_file(Path('gui/ui/error_widget.ui'))
        cls._configure()
        return cls._widget

    @classmethod
    def _configure(cls):
        cls._widget.again_button_err.setCursor(QCursor(Qt.PointingHandCursor))


class ResultsWidget:
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = _load_ui_file(Path('gui/ui/results_widget.ui'))
        cls._configure()
        return cls._widget

    @classmethod
    def _configure(cls):
        cls._widget.again_button_res.setCursor(QCursor(Qt.PointingHandCursor))

    @classmethod
    def set_table_data(cls, data: list[DocumentPairMatch]):
        model = ResultsTableModel(data)
        cls._widget.results_table.setModel(model)
        cls._widget.results_table.resizeRowsToContents()
        cls._widget.results_table.resizeColumnsToContents()


def _load_ui_file(path: Path) -> QMainWindow:
    main_ui = QFile(str(path))
    if not main_ui.open(QIODevice.ReadOnly):
        print(f"Cannot open {path}: {main_ui.errorString()}")
        sys.exit(-1)
    loader = QUiLoader()
    window = loader.load(main_ui)
    main_ui.close()
    if not window:
        print(loader.errorString())
        sys.exit(-1)
    return window
