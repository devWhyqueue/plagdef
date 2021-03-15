import pathlib
from copy import copy
from threading import Thread

import pkg_resources
from PySide6.QtWidgets import QFileDialog, QDialog, QMainWindow, QWidget

from plagdef.gui.model import Config, DocumentPairMatch
from plagdef.gui.views import MainWindow, ConfigureWidget, LoadingWidget, NoResultsWidget, ErrorWidget, ResultsWidget
from plagdef.model import detection
from plagdef.model.legacy.algorithm import InvalidConfigError
from plagdef.model.preprocessing import DocumentFactory, UnsupportedLanguageError
from plagdef.repositories import ConfigFileRepository, DocumentFileRepository, NoDocumentFilePairFoundError, \
    UnsupportedFileFormatError


class WidgetController:
    @classmethod
    def show(cls, data=None):
        cls._widget.parentWidget().setCurrentWidget(cls._widget)

    @classmethod
    def reset(cls):
        pass


class MainWindowController:
    @classmethod
    def create(cls) -> QMainWindow:
        configure_widget = ConfigureWidgetController.create()
        loading_widget = LoadingWidgetController.create()
        error_widget = ErrorWidgetController.create()
        no_res_widget = NoResultsWidgetController.create()
        res_widget = ResultsWidgetController.create()
        cls._window = MainWindow.create(configure_widget, loading_widget, error_widget, no_res_widget, res_widget)
        cls._current_controller = ConfigureWidgetController
        return cls._window

    @classmethod
    def switch_page(cls, widget_controller: type(WidgetController), data=None):
        cls._current_controller.reset()
        widget_controller.show(data=data)
        cls._current_controller = widget_controller


class ConfigureWidgetController(WidgetController):
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = ConfigureWidget.create()
        cls._connect_actions()
        return cls._widget

    @classmethod
    def _connect_actions(cls):
        cls._widget.open_folder_button.clicked.connect(cls._on_open_folder_click)
        cls._widget.remove_folder_button.clicked.connect(cls._on_remove_click)
        cls._widget.radio_buttons.buttonClicked.connect(cls._on_radio_group_click)
        cls._widget.change_lang_button.clicked.connect(cls._on_change_click)
        cls._widget.detect_button.clicked.connect(cls._on_detect_click)

    @classmethod
    def _on_open_folder_click(cls):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec_() == QDialog.Accepted:
            doc_dir = dialog.selectedFiles()[0]
            ConfigureWidget.config.doc_dir = pathlib.Path(doc_dir)
            cls._widget.folder_name_label.setText(
                f'<html><head/><body><p align="center"><span style=" font-size:12pt; color:#ffffff;"> '
                f'{doc_dir[doc_dir.rfind("/"):]}</span></p></body></html>')
            cls._widget.open_folder_button.setVisible(False)
            cls._widget.folder_name_label.setVisible(True)
            cls._widget.remove_folder_button.setVisible(True)
            [radio.setEnabled(True) for radio in cls._widget.radio_buttons.buttons()]

    @classmethod
    def _on_remove_click(cls):
        ConfigureWidget.config.doc_dir = None
        cls._widget.folder_name_label.setVisible(False)
        cls._widget.remove_folder_button.setVisible(False)
        cls._widget.open_folder_button.setVisible(True)
        [radio.setEnabled(False) for radio in cls._widget.radio_buttons.buttons()]

    @classmethod
    def _on_radio_group_click(cls):
        ConfigureWidget.config.lang = 'eng' if cls._widget.radio_buttons.checkedButton().text() == 'English' else 'ger'
        cls._widget.sel_lang_label.setText(
            f'<html><head/><body><p align="center"><span style=" font-size:12pt; color:#ffffff;"> '
            f'{cls._widget.radio_buttons.checkedButton().text()}</span></p></body></html>')
        cls._widget.remove_folder_button.setVisible(False)
        [radio.setVisible(False) for radio in cls._widget.radio_buttons.buttons()]
        cls._widget.sel_lang_label.setVisible(True)
        cls._widget.change_lang_button.setVisible(True)
        cls._widget.detect_button.setEnabled(True)

    @classmethod
    def _on_change_click(cls):
        ConfigureWidget.config.lang = None
        cls._widget.sel_lang_label.setVisible(False)
        cls._widget.change_lang_button.setVisible(False)
        cls._widget.radio_buttons.setExclusive(False)
        cls._widget.radio_buttons.checkedButton().setChecked(False)
        cls._widget.radio_buttons.setExclusive(True)
        [radio.setVisible(True) for radio in cls._widget.radio_buttons.buttons()]
        cls._widget.remove_folder_button.setVisible(True)
        cls._widget.detect_button.setEnabled(False)

    @classmethod
    def _on_detect_click(cls):
        config = copy(ConfigureWidget.config)
        MainWindowController.switch_page(LoadingWidgetController)
        thread = Thread(target=cls._find_matches, args=(config,))
        thread.start()

    @classmethod
    def _find_matches(cls, config: Config):
        try:
            config_path = pkg_resources.resource_filename(__name__, '../config/alg.ini')
            config_repo = ConfigFileRepository(pathlib.Path(config_path))
            alg_config = config_repo.get()
            doc_factory = DocumentFactory(config.lang, alg_config['min_sent_len'], alg_config['rem_stop_words'])
            doc_repo = DocumentFileRepository(config.doc_dir, doc_factory)
            matches = detection.find_matches(doc_repo, config_repo)
            if matches:
                all_matches = []
                for dp_match in matches:
                    for m in dp_match.list():
                        all_matches.append(DocumentPairMatch(dp_match.doc1.name, m.sec1.offset,
                                                             m.sec1.length, dp_match.doc2.name, m.sec2.offset,
                                                             m.sec2.length))
                MainWindowController.switch_page(ResultsWidgetController, data=all_matches)
            else:
                MainWindowController.switch_page(NoResultsWidgetController)
        except (NotADirectoryError, NoDocumentFilePairFoundError, UnsupportedFileFormatError,
                FileNotFoundError, InvalidConfigError, UnsupportedLanguageError) as e:
            MainWindowController.switch_page(ErrorWidgetController, data=str(e))

    @classmethod
    def reset(cls):
        cls._on_change_click()
        cls._on_remove_click()


class LoadingWidgetController(WidgetController):
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = LoadingWidget.create()
        return cls._widget

    @classmethod
    def show(cls, data=None):
        super().show()
        LoadingWidget.start_movie()

    @classmethod
    def reset(cls):
        super().reset()
        LoadingWidget.stop_movie()


class NoResultsWidgetController(WidgetController):
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = NoResultsWidget.create()
        cls._connect_actions()
        return cls._widget

    @classmethod
    def _connect_actions(cls):
        cls._widget.again_button_no_res.clicked.connect(cls._on_again_click)

    @classmethod
    def _on_again_click(cls):
        MainWindowController.switch_page(ConfigureWidgetController)


class ErrorWidgetController(WidgetController):
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = ErrorWidget.create()
        cls._connect_actions()
        return cls._widget

    @classmethod
    def _connect_actions(cls):
        cls._widget.again_button_err.clicked.connect(cls._on_again_click)

    @classmethod
    def _on_again_click(cls):
        MainWindowController.switch_page(ConfigureWidgetController)

    @classmethod
    def show(cls, data=None):
        super().show()
        cls._widget.error_msg_label.setText(
            f'<html><head/><body><p align="center"><span style=" font-size:12pt; color:#ffffff;"> '
            f'{data}</span></p></body></html>')


class ResultsWidgetController(WidgetController):
    @classmethod
    def create(cls) -> QWidget:
        cls._widget = ResultsWidget.create()
        cls._connect_actions()
        return cls._widget

    @classmethod
    def _connect_actions(cls):
        cls._widget.again_button_res.clicked.connect(cls._on_again_click)

    @classmethod
    def _on_again_click(cls):
        MainWindowController.switch_page(ConfigureWidgetController)

    @classmethod
    def show(cls, data=None):
        super().show()
        ResultsWidget.set_table_data(data)
