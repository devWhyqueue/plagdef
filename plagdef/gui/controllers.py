import os
import platform
import subprocess

import plagdef.gui.main as main
from plagdef.app import write_doc_pair_matches_to_json, read_doc_pair_matches_from_json
from plagdef.gui.views import HomeView, LoadingView, NoResultsView, ErrorView, ResultView, \
    FileDialog, MatchesDialog, MessageDialog, SettingsDialog
from plagdef.model.models import DocumentPairMatches
from plagdef.services import update_config


class HomeController:
    def __init__(self):
        self.view = HomeView()
        self.settings_dialog = SettingsDialog()
        self.archive_dir_dialog = FileDialog()
        self.docs_dir_dialog = FileDialog()
        self.common_dir_dialog = FileDialog()
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(select_lang=self.on_select_lang,
                                       open_report_dir=self.on_open_click,
                                       select_archive_dir=self._on_select_archive_dir,
                                       rm_archive_dir=self._on_remove_archive_dir,
                                       select_docs_dir=self._on_select_docs_dir,
                                       rm_docs_dir=self._on_remove_docs_dir,
                                       select_common_dir=self._on_select_common_dir,
                                       rm_common_dir=self._on_remove_common_dir,
                                       detect=self._on_detect,
                                       settings=self._on_settings_click)

    def on_select_lang(self):
        update_config({'lang': self.view.lang})

    def on_open_click(self):
        dialog = FileDialog()
        if dialog.open():
            matches = read_doc_pair_matches_from_json(dialog.selected_dir)
            if len(matches):
                main.app.window.switch_to(ResultView, matches)
            else:
                MessageDialog('The selected folder contains no match files.')

    def _on_settings_click(self):
        self.settings_dialog.open()
        update_config({'ocr': self.settings_dialog.ocr,
                       'min_cos_sim': self.settings_dialog.similarity_threshold,
                       'min_dice_sim': self.settings_dialog.similarity_threshold,
                       'min_cluster_cos_sim': self.settings_dialog.similarity_threshold})

    def _on_select_archive_dir(self):
        if self.archive_dir_dialog.open():
            folder_name = self.archive_dir_dialog.selected_dir[self.archive_dir_dialog.selected_dir.rfind("/"):]
            self.view.archive_dir_selected(folder_name)

    def _on_remove_archive_dir(self):
        self.archive_dir_dialog.selected_dir = None
        self.view.archive_dir_removed()

    def _on_select_docs_dir(self):
        if self.docs_dir_dialog.open():
            folder_name = self.docs_dir_dialog.selected_dir[self.docs_dir_dialog.selected_dir.rfind("/"):]
            self.view.docs_dir_selected(folder_name)

    def _on_remove_docs_dir(self):
        self.docs_dir_dialog.selected_dir = None
        self.view.docs_dir_removed()

    def _on_select_common_dir(self):
        if self.common_dir_dialog.open():
            folder_name = self.common_dir_dialog.selected_dir[self.common_dir_dialog.selected_dir.rfind("/"):]
            self.view.common_dir_selected(folder_name)

    def _on_remove_common_dir(self):
        self.common_dir_dialog.selected_dir = None
        self.view.common_dir_removed()

    def _on_detect(self):
        doc_dir = (self.docs_dir_dialog.selected_dir, self.view.docs_rec) if self.docs_dir_dialog.selected_dir else None
        archive_dir = (self.archive_dir_dialog.selected_dir, self.view.archive_rec) \
            if self.archive_dir_dialog.selected_dir else None
        common_dir = (self.common_dir_dialog.selected_dir, self.view.common_rec) \
            if self.common_dir_dialog.selected_dir else None
        main.app.find_matches(doc_dir, archive_dir, common_dir)
        main.app.window.switch_to(LoadingView)
        self.archive_dir_dialog.selected_dir = self.common_dir_dialog.selected_dir \
            = self.docs_dir_dialog.selected_dir = None


class LoadingController:
    def __init__(self):
        self.view = LoadingView()


class NoResultsController:
    def __init__(self):
        self.view = NoResultsView()
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(self._on_again)

    def _on_again(self):
        main.app.window.switch_to(HomeView)


class ErrorController:
    def __init__(self):
        self.view = ErrorView()
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(self._on_again)

    def _on_again(self):
        main.app.window.switch_to(HomeView)


class ResultController:
    def __init__(self):
        self.view = ResultView()
        self.matches_dialog = MatchesDialog()
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(self.on_export, self._on_again, self.on_select_pair)
        self.matches_dialog.register_for_signals(self.on_prev_match, self.on_next_match, self.on_doc_name_click)

    def on_export(self):
        selected_matches = self.view.selected_matches
        if not selected_matches:
            MessageDialog(f"Please select matches first!")
        else:
            dialog = FileDialog()
            if dialog.open():
                write_doc_pair_matches_to_json(selected_matches, dialog.selected_dir)
                MessageDialog(f"Successfully generated {len(selected_matches)} JSON report(s).")

    def _on_again(self):
        main.app.window.switch_to(HomeView)

    def on_select_pair(self, doc_pair_matches: DocumentPairMatches):
        self.matches_dialog.open(doc_pair_matches)

    def on_prev_match(self):
        self.matches_dialog.prev_match()

    def on_next_match(self):
        self.matches_dialog.next_match()

    def on_doc_name_click(self, path: str):
        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', path))
        elif platform.system() == 'Windows':  # Windows
            os.startfile(path)
        else:  # linux variants
            subprocess.call(('xdg-open', path))
