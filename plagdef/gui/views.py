from __future__ import annotations

import sys
from pathlib import Path

import pkg_resources
from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtGui import QCursor, QMovie
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QButtonGroup, QMainWindow, QFileDialog, QDialog

from plagdef.gui.model import ResultsTableModel, DocumentPairMatches

UI_FILES = {
    'main_window': pkg_resources.resource_filename(__name__, 'ui/main_window.ui'),
    'home_widget': pkg_resources.resource_filename(__name__, 'ui/home_widget.ui'),
    'loading_widget': pkg_resources.resource_filename(__name__, 'ui/loading_widget.ui'),
    'error_widget': pkg_resources.resource_filename(__name__, 'ui/error_widget.ui'),
    'no_results_widget': pkg_resources.resource_filename(__name__, 'ui/no_results_widget.ui'),
    'results_widget': pkg_resources.resource_filename(__name__, 'ui/results_widget.ui'),
    'matches_dialog': pkg_resources.resource_filename(__name__, 'ui/matches_dialog.ui'),
}


class MainWindow:
    def __init__(self, views: list[View]):
        self._window = _load_ui_file(Path(UI_FILES['main_window']))
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
        self.lang = 'ger'
        self.archive_rec = self.docs_rec = self.common_rec = False
        self.widget = _load_ui_file(Path(UI_FILES['home_widget']))
        self._configure()

    def _configure(self):
        self.widget.lang_button_group = QButtonGroup()
        self.widget.lang_button_group.addButton(self.widget.ger_button)
        self.widget.lang_button_group.addButton(self.widget.eng_button)
        [element.setVisible(False)
         for element in (self.widget.archive_dir_label, self.widget.archive_rmdir_button, self.widget.docs_dir_label,
                         self.widget.docs_rmdir_button, self.widget.common_dir_label, self.widget.common_rmdir_button)]
        [button.setCursor(QCursor(Qt.PointingHandCursor))
         for button in (self.widget.ger_button, self.widget.eng_button, self.widget.archive_dir_button,
                        self.widget.docs_dir_button, self.widget.common_dir_button, self.widget.detect_button,
                        self.widget.archive_rmdir_button, self.widget.docs_rmdir_button,
                        self.widget.common_rmdir_button)]

    def register_for_signals(self, select_archive_dir=None, rm_archive_dir=None, select_docs_dir=None,
                             rm_docs_dir=None, select_common_dir=None, rm_common_dir=None):
        self.widget.archive_dir_button.clicked.connect(lambda: select_archive_dir())
        self.widget.archive_rmdir_button.clicked.connect(lambda: rm_archive_dir())
        self.widget.docs_dir_button.clicked.connect(lambda: select_docs_dir())
        self.widget.docs_rmdir_button.clicked.connect(lambda: rm_docs_dir())
        self.widget.common_dir_button.clicked.connect(lambda: select_common_dir())
        self.widget.common_rmdir_button.clicked.connect(lambda: rm_common_dir())

    def archive_dir_selected(self, folder_name: str):
        self._dir_selected(folder_name, self.widget.archive_dir_button, self.widget.archive_rmdir_button,
                           self.widget.archive_dir_label, 12)

    def archive_dir_removed(self):
        self._dir_removed(self.widget.archive_dir_button, self.widget.archive_rmdir_button,
                          self.widget.archive_dir_label)

    def docs_dir_selected(self, folder_name: str):
        self._dir_selected(folder_name, self.widget.docs_dir_button, self.widget.docs_rmdir_button,
                           self.widget.docs_dir_label, 16)
        self.widget.detect_button.setEnabled(True)

    def docs_dir_removed(self):
        self._dir_removed(self.widget.docs_dir_button, self.widget.docs_rmdir_button, self.widget.docs_dir_label)
        self.widget.detect_button.setEnabled(False)

    def common_dir_selected(self, folder_name: str):
        self._dir_selected(folder_name, self.widget.common_dir_button, self.widget.common_rmdir_button,
                           self.widget.common_dir_label, 12)

    def common_dir_removed(self):
        self._dir_removed(self.widget.common_dir_button, self.widget.common_rmdir_button, self.widget.common_dir_label)

    def _dir_selected(self, folder_name: str, dir_button, rm_button, label, font_size: int):
        dir_button.setEnabled(False)
        label.setText(
            f'<html><head/><body><p align="center"><span style="font-size:{font_size}pt; color:#ffffff;"> '
            f'{folder_name}</span></p></body></html>')
        label.setVisible(True)
        rm_button.setVisible(True)

    def _dir_removed(self, button, rm_button, label):
        label.setVisible(False)
        rm_button.setVisible(False)
        button.setEnabled(True)

    def on_destroy(self):
        self.archive_dir_removed()
        self.docs_dir_removed()
        self.common_dir_removed()


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
        self.widget = _load_ui_file(Path(UI_FILES['loading_widget']))
        self._configure()

    def _configure(self):
        self.widget.loading_movie_label.setMovie(self._movie)

    def on_init(self, data=None):
        self._movie.start()

    def on_destroy(self):
        self._movie.stop()


class NoResultsView(View):
    def __init__(self):
        self.widget = _load_ui_file(Path(UI_FILES['no_results_widget']))
        self._configure()

    def _configure(self):
        self.widget.again_button_no_res.setCursor(QCursor(Qt.PointingHandCursor))

    def register_for_signals(self, again=None):
        self.widget.again_button_no_res.clicked.connect(lambda: again())


class ErrorView(View):
    def __init__(self):
        self.widget = _load_ui_file(Path(UI_FILES['error_widget']))
        self._configure()

    def _configure(self):
        self.widget.again_button_err.setCursor(QCursor(Qt.PointingHandCursor))

    def on_init(self, data=None):
        self.widget.error_msg_label.setText(
            f'<html><head/><body><p align="center"><span style=" font-size:12pt; color:#ffffff;"> '
            f'{data}</span></p></body></html>')
        self.widget.error_msg_label.setWordWrap(True)

    def register_for_signals(self, again=None):
        self.widget.again_button_err.clicked.connect(lambda: again())


class ResultView(View):
    def __init__(self):
        self.widget = _load_ui_file(Path(UI_FILES['results_widget']))
        self._configure()

    def _configure(self):
        self.widget.again_button_res.setCursor(QCursor(Qt.PointingHandCursor))

    def on_init(self, data=None):
        self.widget.doc_pairs_label.setText(f"Found {len(data)} suspicious document pair"
                                            f"{'s' if len(data) > 1 else ''}.")
        model = ResultsTableModel(data)
        self.widget.results_table.setModel(model)
        self.widget.results_table.resizeRowsToContents()
        self.widget.results_table.resizeColumnsToContents()

    def register_for_signals(self, again=None, select_pair=None):
        self.widget.again_button_res.clicked.connect(lambda: again())
        self.widget.results_table.doubleClicked.connect(
            lambda index: select_pair(index.model().doc_pair_matches(index)))


class MatchesDialog:
    def __init__(self):
        self.widget = _load_ui_file(Path(UI_FILES['matches_dialog']))
        self._doc_pair_matches = None
        self._selected = 0

    def open(self, doc_pair_matches: DocumentPairMatches):
        self._doc_pair_matches = doc_pair_matches
        self.widget.doc1_label.setText(self._doc_pair_matches.doc1.name)
        self.widget.doc1_path.setText(f'({self._doc_pair_matches.doc1.path})')
        self.widget.doc2_label.setText(self._doc_pair_matches.doc2.name)
        self.widget.doc2_path.setText(f'({self._doc_pair_matches.doc2.path})')
        self._selected = 0
        self._show_match()
        self.widget.exec_()

    def _show_match(self):
        doc1, doc2 = self._doc_pair_matches.doc1, self._doc_pair_matches.doc2
        self.widget.doc1_text.setText(self._doc_pair_matches.matches[self._selected].frag_from_doc(doc1).text)
        self.widget.doc2_text.setText(self._doc_pair_matches.matches[self._selected].frag_from_doc(doc2).text)
        self.widget.page_label.setText(f'{self._selected + 1}/{len(self._doc_pair_matches)}')
        self.widget.prev_button.setVisible(True)
        self.widget.next_button.setVisible(True)
        if self._selected == 0:
            self.widget.prev_button.setVisible(False)
        if self._selected + 1 == len(self._doc_pair_matches):
            self.widget.next_button.setVisible(False)

    def register_for_signals(self, prev_match=None, next_match=None):
        self.widget.prev_button.clicked.connect(lambda: prev_match())
        self.widget.next_button.clicked.connect(lambda: next_match())

    def prev_match(self):
        self._selected -= 1
        self._show_match()

    def next_match(self):
        self._selected += 1
        self._show_match()


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
