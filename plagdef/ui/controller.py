from PySide6.QtWidgets import QFileDialog, QDialog

from plagdef.ui.views import MainWindowFactory


class MainWindowController:
    def __init__(self):
        self._main_window = MainWindowFactory.create()
        self._connect_actions()

    def _connect_actions(self):
        self._main_window.open_folder_button.clicked.connect(self._on_open_folder_click)
        self._main_window.remove_folder_button.clicked.connect(self._on_remove_click)
        self._main_window.radio_buttons.buttonClicked.connect(self._on_radio_group_click)
        self._main_window.change_lang_button.clicked.connect(self._on_change_click)

    def _on_open_folder_click(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec_() == QDialog.Accepted:
            self._doc_dir_path = dialog.selectedFiles()[0]
            self._main_window.folder_name_label.setText(
                f'<html><head/><body><p align="center"><span style=" font-size:12pt; color:#ffffff;"> '
                f'{self._doc_dir_path[self._doc_dir_path.rfind("/"):]}</span></p></body></html>')
            self._main_window.open_folder_button.setVisible(False)
            self._main_window.folder_name_label.setVisible(True)
            self._main_window.remove_folder_button.setVisible(True)
            [radio.setEnabled(True) for radio in self._main_window.radio_buttons.buttons()]

    def _on_remove_click(self):
        self._doc_dir_path = None
        self._main_window.folder_name_label.setVisible(False)
        self._main_window.remove_folder_button.setVisible(False)
        self._main_window.open_folder_button.setVisible(True)
        [radio.setEnabled(False) for radio in self._main_window.radio_buttons.buttons()]

    def _on_radio_group_click(self):
        self._lang = 'eng' if self._main_window.radio_buttons.checkedButton().text() == 'English' else 'ger'
        self._main_window.sel_lang_label.setText(
            f'<html><head/><body><p align="center"><span style=" font-size:12pt; color:#ffffff;"> '
            f'{self._main_window.radio_buttons.checkedButton().text()}</span></p></body></html>')
        self._main_window.remove_folder_button.setVisible(False)
        [radio.setVisible(False) for radio in self._main_window.radio_buttons.buttons()]
        self._main_window.sel_lang_label.setVisible(True)
        self._main_window.change_lang_button.setVisible(True)
        self._main_window.detect_button.setEnabled(True)

    def _on_change_click(self):
        self._lang = None
        self._main_window.sel_lang_label.setVisible(False)
        self._main_window.change_lang_button.setVisible(False)
        self._main_window.radio_buttons.setExclusive(False)
        self._main_window.radio_buttons.checkedButton().setChecked(False)
        self._main_window.radio_buttons.setExclusive(True)
        [radio.setVisible(True) for radio in self._main_window.radio_buttons.buttons()]
        self._main_window.remove_folder_button.setVisible(True)
        self._main_window.detect_button.setEnabled(False)

    def show(self):
        self._main_window.show()
