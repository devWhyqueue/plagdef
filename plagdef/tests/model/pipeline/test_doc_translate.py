from pathlib import Path
from shutil import copy2
from unittest.mock import patch, PropertyMock

import pytest
from selenium.common import TimeoutException

from plagdef.model.models import Document
from plagdef.model.pipeline.doc_translate import translate_doc, TranslationError, _save_to_pdf, _extract_text, \
    _translate_pdf


@patch("plagdef.model.pipeline.doc_translate._save_to_pdf")
@patch("plagdef.model.pipeline.doc_translate.ChromeService", return_value="path/to/chromedriver")
@patch("plagdef.model.pipeline.doc_translate.webdriver.Edge")
@patch("plagdef.model.pipeline.doc_translate._translate_pdf")
def test_translate_fails_if_google_does_not_translate(translate_mock, driver_mock, svc_mock, to_pdf_mock, tmp_path):
    driver_mock.return_value.__enter__.return_value.name = "webdriver"
    doc = Document("doc", "/some/path/doc.txt", "This should be translated but is not.")
    pdf_file = _save_to_pdf(doc, str(tmp_path))
    to_pdf_mock.return_value = pdf_file
    copy2(pdf_file, Path(pdf_file).with_suffix(".old"))
    with pytest.raises(TranslationError):
        translate_doc(doc, "de")


@patch("plagdef.model.pipeline.doc_translate.WebDriverWait", side_effect=TimeoutException())
def test_translate_fails_if_wait_time_is_exceeded(wait_mock):
    with pytest.raises(TranslationError):
        _translate_pdf(None, "/path/to/pdf", "de")


@patch('plagdef.model.pipeline.doc_translate.PdfReader.pages', new_callable=PropertyMock)
def test_save_to_pdf_fails_with_doc_over_300_pages(reader_mock, tmp_path):
    reader_mock.return_value = range(301)
    doc = Document("doc", "/some/path/doc.txt", "This text is too long.")
    with pytest.raises(TranslationError):
        _save_to_pdf(doc, str(tmp_path))


def test_save_to_pdf_and_extract_does_not_alter_text(tmp_path):
    doc = Document("doc", "/some/path/doc.txt",
                   "The English army of some 10,000 men had landed in northern Normandy on 12 July 1346. They "
                   "embarked on a large-scale raid, or chevauchée, devastating large parts of northern France. On 26 "
                   "August 1346, fighting on ground of their own choosing, the English inflicted a heavy defeat on a "
                   "large French army led by their king Philip VI at the Battle of Crécy. A week later they invested "
                   "the well-fortified port of Calais, which had a strong garrison under the command of Jean de "
                   "Vienne.")
    pdf_file = _save_to_pdf(doc, str(tmp_path))
    extracted_text = _extract_text(pdf_file)
    assert doc.text == extracted_text.replace("\n", " ")
