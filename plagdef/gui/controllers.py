import plagdef.gui.main as main
from plagdef.gui.views import HomeView, LoadingView, NoResultsView, ErrorView, ResultView, \
    FileDialog, MatchesDialog
from plagdef.model.models import DocumentPairMatches


class HomeController:
    def __init__(self):
        self.view = HomeView()
        self.doc_dir_dialog = FileDialog()
        self.common_doc_dir_dialog = FileDialog()
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(open_folder=self._on_open_folder, exclude_common=self.on_exclude_common,
                                       remove_folder=self._on_remove_folder, select_lang=self._on_select_lang,
                                       reset_lang_sel=self._on_reset_lang, detect=self._on_detect)

    def _on_open_folder(self):
        if self.doc_dir_dialog.open():
            folder_name = self.doc_dir_dialog.selected_dir[self.doc_dir_dialog.selected_dir.rfind("/"):]
            self.view.folder_selected(folder_name)

    def on_exclude_common(self, checked: bool):
        if checked:
            if self.common_doc_dir_dialog.open():
                folder_name = self.common_doc_dir_dialog.selected_dir[
                              self.common_doc_dir_dialog.selected_dir.rfind("/"):]
                self.view.common_folder_selected(folder_name)
            else:
                self.view.reset_exclude_common()
        else:
            self.view.reset_exclude_common()

    def _on_remove_folder(self):
        self.view.reset_folder_selection()

    def _on_select_lang(self):
        self.view.language_selected()

    def _on_reset_lang(self):
        self.view.reset_language_selection()

    def _on_detect(self):
        main.app.find_matches(self.view.lang, self.doc_dir_dialog.selected_dir, self.view.recursive,
                              self.common_doc_dir_dialog.selected_dir)
        main.app.window.switch_to(LoadingView)
        self.common_doc_dir_dialog.selected_dir = None


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
        self.view.register_for_signals(self._on_again, self.on_select_pair)
        self.matches_dialog.register_for_signals(self.on_prev_match, self.on_next_match)

    def _on_again(self):
        main.app.window.switch_to(HomeView)

    def on_select_pair(self, doc_pair_matches: DocumentPairMatches):
        self.matches_dialog.open(doc_pair_matches)

    def on_prev_match(self):
        self.matches_dialog.prev_match()

    def on_next_match(self):
        self.matches_dialog.next_match()
