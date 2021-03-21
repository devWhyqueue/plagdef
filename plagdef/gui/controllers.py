import plagdef.gui.main as main
from plagdef.gui.views import HomeView, LoadingView, NoResultsView, ErrorView, ResultView, \
    FileDialog


class HomeController:
    def __init__(self):
        self.view = HomeView()
        self.file_dialog = FileDialog()
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(open_folder=self._on_open_folder, remove_folder=self._on_remove_folder,
                                       select_lang=self._on_select_lang, reset_lang_sel=self._on_reset_lang,
                                       detect=self._on_detect)

    def _on_open_folder(self):
        if self.file_dialog.open():
            folder_name = self.file_dialog.selected_dir[self.file_dialog.selected_dir.rfind("/"):]
            self.view.folder_selected(folder_name)

    def _on_remove_folder(self):
        self.view.reset_folder_selection()

    def _on_select_lang(self):
        self.view.language_selected()

    def _on_reset_lang(self):
        self.view.reset_language_selection()

    def _on_detect(self):
        main.app.find_matches(self.file_dialog.selected_dir, self.view.lang, recursive=self.view.recursive)
        main.app.window.switch_to(LoadingView)


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
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(self._on_again)

    def _on_again(self):
        main.app.window.switch_to(HomeView)
