from __future__ import annotations

import sys
import traceback
from collections import Callable

from PySide6.QtCore import QThreadPool, QRunnable, Slot, QObject, Signal
from PySide6.QtWidgets import QApplication
from click import UsageError

# noinspection PyUnresolvedReferences
import plagdef.gui.resources
from plagdef.gui.controllers import HomeController, LoadingController, ErrorController, NoResultsController, \
    ResultController
from plagdef.gui.views import MainWindow, ResultView, NoResultsView, ErrorView
from plagdef.model.models import DocumentPairMatches

app = None


class MyQtApp(QApplication):
    def __init__(self, find_matches: Callable):
        super().__init__()
        self._ctrls = [HomeController(), LoadingController(), ErrorController(), NoResultsController(),
                       ResultController()]
        self._views = [ctrl.view for ctrl in self._ctrls]
        self.window = MainWindow(self._views)
        self._find_matches = find_matches
        global app
        app = self

    def find_matches(self, doc_dir: str, lang: str, recursive=False):
        worker = Worker(self._find_matches, doc_dir, lang, recursive=recursive)
        worker.signals.result.connect(self._on_success)
        worker.signals.error.connect(self._on_error)
        pool = QThreadPool.globalInstance()
        pool.start(worker)

    def _on_success(self, matches: list[DocumentPairMatches]):
        if matches:
            self.window.switch_to(ResultView, matches)
        else:
            self.window.switch_to(NoResultsView)

    def _on_error(self, error: (type, Exception)):
        if error[0] == UsageError:
            self.window.switch_to(ErrorView, str(error[1]))
        else:
            self.window.switch_to(ErrorView, 'An error occurred. Please refer to the command line for more details.')
            raise error[1]


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)


class WorkerSignals(QObject):
    error = Signal(tuple)
    result = Signal(object)
