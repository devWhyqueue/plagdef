import multiprocessing
import pathlib

from click import UsageError

from plagdef.gui.views import MainWindow, HomeView, LoadingView, NoResultsView, ErrorView, ResultView, \
    FileDialog
from plagdef.model.legacy.algorithm import DocumentPairMatches


class MainWindowController:
    @classmethod
    def init(cls, find_matches):
        views = [HomeController().view, LoadingController().view, ErrorController().view,
                 NoResultsController().view, ResultController().view]
        cls.window = MainWindow(views)
        cls._find_matches = find_matches

    @classmethod
    def switch_to(cls, view_cls: type, data=None):
        cls.window.switch_to(view_cls, data)

    @classmethod
    def find_matches(cls, doc_dir: str, lang: str):
        cls.switch_to(LoadingView)
        cls._pool = multiprocessing.Pool()
        cls._pool.apply_async(cls._find_matches, (pathlib.Path(doc_dir), lang), callback=cls._on_success,
                              error_callback=cls._on_error)

    @classmethod
    def _on_success(cls, matches: list[DocumentPairMatches]):
        cls._pool.close()
        if matches:
            cls.switch_to(ResultView, matches)
        else:
            cls.switch_to(NoResultsView)

    @classmethod
    def _on_error(cls, error: Exception):
        cls._pool.close()
        if isinstance(error, UsageError):
            cls.switch_to(ErrorView, str(error))
        else:
            cls.switch_to(ErrorView, 'An error occurred. Please refer to the command line for more details.')
            raise error


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
            self.view.show_folder_name(folder_name)
            self.view.enable_language_selection(True)

    def _on_remove_folder(self):
        self.view.show_open_folder_button(True)
        self.view.enable_language_selection(False)

    def _on_select_lang(self):
        self.view.language_selection_completed(True)

    def _on_reset_lang(self):
        self.view.reset_language_selection()
        self.view.language_selection_completed(False)

    def _on_detect(self):
        MainWindowController.find_matches(self.file_dialog.selected_dir, self.view.lang)


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
        MainWindowController.switch_to(HomeView)


class ErrorController:
    def __init__(self):
        self.view = ErrorView()
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(self._on_again)

    def _on_again(self):
        MainWindowController.switch_to(HomeView)


class ResultController:
    def __init__(self):
        self.view = ResultView()
        self._connect_slots()

    def _connect_slots(self):
        self.view.register_for_signals(self._on_again)

    def _on_again(self):
        MainWindowController.switch_to(HomeView)
