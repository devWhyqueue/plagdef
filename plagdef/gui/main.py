from __future__ import annotations

import os
import signal
from collections import Callable
from concurrent.futures import ThreadPoolExecutor, Future

from PySide6.QtWidgets import QApplication
from click import UsageError

# noinspection PyUnresolvedReferences
import plagdef.gui.resources
from plagdef.gui.controllers import HomeController, LoadingController, ErrorController, NoResultsController, \
    ResultController
from plagdef.gui.views import MainWindow, ResultView, NoResultsView, ErrorView

app = None


class MyQtApp(QApplication):
    def __init__(self, find_matches: Callable):
        super().__init__()
        self.aboutToQuit.connect(lambda: os.kill(os.getpid(), signal.SIGINT))
        self._ctrls = [HomeController(), LoadingController(), ErrorController(), NoResultsController(),
                       ResultController()]
        self._views = [ctrl.view for ctrl in self._ctrls]
        self.window = MainWindow(self._views)
        self._find_matches = find_matches
        global app
        app = self

    def find_matches(self, lang: str, doc_dir: str, recursive: bool, common_doc_dir: str):
        pool = ThreadPoolExecutor()
        future = pool.submit(self._find_matches, lang, doc_dir, recursive=recursive,
                             common_doc_dir=common_doc_dir)
        future.add_done_callback(self._on_completion)
        pool.shutdown(wait=False)

    def _on_completion(self, future: Future):
        error = future.exception()
        if error:
            if type(error) == UsageError:
                self.window.switch_to(ErrorView, str(error))
            else:
                self.window.switch_to(ErrorView,
                                      'An error occurred. Please refer to the command line for more details.')
                raise error
        else:
            matches = future.result()
            if len(matches):
                self.window.switch_to(ResultView, matches)
            else:
                self.window.switch_to(NoResultsView)
