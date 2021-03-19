from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtGui import QCursor, QMovie
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QButtonGroup, QMainWindow, QFileDialog, QDialog

from plagdef.gui.model import ResultsTableModel


class MainWindow:
    def __init__(self, views: list[View]):
        self._window = _load_ui_file(Path('gui/ui/main_window.ui'))
        self._views = views
        self._configure()

    def _configure(self):
        for view in self._views:
            self._window.stacked_widget.addWidget(view.widget)

    def switch_to(self, view_cls: type, data=None):
        idx = self._window.stacked_widget.currentIndex()
        for view in self._views:
            if type(view) == view_cls:
                self._views[idx].on_destroy()
                self._window.stacked_widget.setCurrentWidget(view.widget)
                view.on_init(data)

    def show(self):
        self._window.show()


class View:
    def on_init(self, data=None):
        pass

    def on_destroy(self):
        pass


class HomeView(View):
    def __init__(self):
        self.lang = None
        self.widget = _load_ui_file(Path('gui/ui/home_widget.ui'))
        self._configure()

    def _configure(self):
        self.widget.lang_button_group = QButtonGroup()
        self.widget.lang_button_group.addButton(self.widget.eng_radio)
        self.widget.lang_button_group.addButton(self.widget.ger_radio)
        self.widget.open_folder_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.widget.detect_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.widget.folder_name_label.setVisible(False)
        self.widget.remove_folder_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.widget.remove_folder_button.setVisible(False)
        self.widget.sel_lang_label.setVisible(False)
        self.widget.change_lang_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.widget.change_lang_button.setVisible(False)

    def register_for_signals(self, open_folder=None, remove_folder=None, select_lang=None,
                             reset_lang_sel=None, detect=None):
        self.widget.open_folder_button.clicked.connect(lambda: open_folder())
        self.widget.remove_folder_button.clicked.connect(lambda: remove_folder())
        self.widget.lang_button_group.buttonClicked.connect(lambda: select_lang())
        self.widget.change_lang_button.clicked.connect(lambda: reset_lang_sel())
        self.widget.detect_button.clicked.connect(lambda: detect())

    def show_folder_name(self, folder_name: str):
        self.widget.folder_name_label.setText(
            f'<html><head/><body><p align="center"><span style="font-size:12pt; color:#ffffff;"> '
            f'{folder_name}</span></p></body></html>')
        self.widget.open_folder_button.setVisible(False)
        self.widget.folder_name_label.setVisible(True)
        self.show_open_folder_button(False)

    def enable_language_selection(self, enabled: bool):
        [radio.setEnabled(enabled) for radio in self.widget.lang_button_group.buttons()]

    def show_open_folder_button(self, visible: bool):
        self.widget.folder_name_label.setVisible(not visible)
        self.widget.remove_folder_button.setVisible(not visible)
        self.widget.open_folder_button.setVisible(visible)

    def language_selection_completed(self, completed: bool):
        self.widget.remove_folder_button.setVisible(not completed)
        [radio.setVisible(not completed) for radio in self.widget.lang_button_group.buttons()]
        self.widget.sel_lang_label.setVisible(completed)
        self.widget.change_lang_button.setVisible(completed)
        self.widget.detect_button.setEnabled(completed)
        if completed:
            lang_long = self.widget.lang_button_group.checkedButton().text()
            self.lang = lang_long[:3].lower()
            self.widget.sel_lang_label.setText(
                f'<html><head/><body><p align="center"><span style="font-size:12pt; color:#ffffff;"> '
                f'{lang_long}</span></p></body></html>')

    def reset_language_selection(self):
        self.lang = None
        self.widget.lang_button_group.setExclusive(False)
        self.widget.lang_button_group.checkedButton().setChecked(False)
        self.widget.lang_button_group.setExclusive(True)

    def on_destroy(self):
        self.reset_language_selection()
        self.language_selection_completed(False)
        self.enable_language_selection(False)
        self.show_open_folder_button(True)
        self.widget.detect_button.setEnabled(False)


class FileDialog(QFileDialog):
    def __init__(self):
        super().__init__()
        self.setFileMode(QFileDialog.Directory)
        self.selected_dir = None

    def open(self) -> bool:
        if self.exec_() == QDialog.Accepted:
            self.selected_dir = self.selectedFiles()[0]
            return True


class LoadingView(View):
    def __init__(self):
        self._movie = QMovie(':/loading.gif')
        self.widget = _load_ui_file(Path('gui/ui/loading_widget.ui'))
        self._configure()

    def _configure(self):
        self.widget.loading_movie_label.setMovie(self._movie)

    def on_init(self, data=None):
        self._movie.start()

    def on_destroy(self):
        self._movie.stop()


class NoResultsView(View):
    def __init__(self):
        self.widget = _load_ui_file(Path('gui/ui/no_results_widget.ui'))
        self._configure()

    def _configure(self):
        self.widget.again_button_no_res.setCursor(QCursor(Qt.PointingHandCursor))

    def register_for_signals(self, again=None):
        self.widget.again_button_no_res.clicked.connect(lambda: again())


class ErrorView(View):
    def __init__(self):
        self.widget = _load_ui_file(Path('gui/ui/error_widget.ui'))
        self._configure()

    def _configure(self):
        self.widget.again_button_err.setCursor(QCursor(Qt.PointingHandCursor))

    def on_init(self, data=None):
        self.widget.error_msg_label.setText(
            f'<html><head/><body><p align="center"><span style=" font-size:12pt; color:#ffffff;"> '
            f'{data}</span></p></body></html>')

    def register_for_signals(self, again=None):
        self.widget.again_button_err.clicked.connect(lambda: again())


class ResultView(View):
    def __init__(self):
        self.widget = _load_ui_file(Path('gui/ui/results_widget.ui'))
        self._configure()

    def _configure(self):
        self.widget.again_button_res.setCursor(QCursor(Qt.PointingHandCursor))

    def on_init(self, data=None):
        model = ResultsTableModel(data)
        self.widget.results_table.setModel(model)
        self.widget.results_table.resizeRowsToContents()
        self.widget.results_table.resizeColumnsToContents()

    def register_for_signals(self, again=None):
        self.widget.again_button_res.clicked.connect(lambda: again())


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
