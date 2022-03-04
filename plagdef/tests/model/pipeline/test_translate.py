from unittest.mock import patch

from deep_translator import GoogleTranslator

from plagdef.model.models import Document
from plagdef.model.pipeline.translate import detect_lang, docs_in_other_langs, translate, _split_text_at_punct


def test_detect_lang():
    doc = Document('doc', 'path/to/doc', 'This is an English document.')
    detect_lang({doc})
    assert doc.lang == "en"


def test_detect_lang_with_multiple_docs():
    doc1 = Document('doc1', 'path/to/doc1', 'This is an English document.')
    doc2 = Document('doc2', 'path/to/doc2', 'Das ist ein deutsches Dokument.')
    detect_lang([doc1, doc2])
    assert doc1.lang == "en"
    assert doc2.lang == "de"


def test_detect_lang_with_empty_doc():
    doc = Document('doc', 'path/to/doc', '')
    detect_lang({doc})
    assert doc.lang is None


def test_docs_in_other_langs():
    doc0 = Document('doc0', 'path/to/doc0', '')
    doc1 = Document('doc1', 'path/to/doc1', 'This is an English document.')
    doc2 = Document('doc2', 'path/to/doc2', 'Das ist ein deutsches Dokument.')
    doc3 = Document('doc3', 'path/to/doc3', 'Das ist ein weiteres deutsches Dokument.')
    doc1.lang, doc2.lang, doc3.lang = "en", "de", "de"
    other_docs = docs_in_other_langs({doc0, doc1, doc2, doc3}, "de")
    assert other_docs == {doc0, doc1}


@patch.object(GoogleTranslator, "translate", return_value="Hallo Welt!")
def test_translate(t_mock):
    doc = Document('doc', 'path/to/doc', "Hello World!")
    doc.lang = "en"
    translate({doc}, "de")
    assert doc.text == "Hallo Welt!"


@patch.object(GoogleTranslator, "translate", return_value="Dies ist ein englisches Dokument.")
def test_translate_with_multiple_docs(t_mock):
    doc1 = Document('doc1', 'path/to/doc1', 'This is an English document.')
    doc2 = Document('doc2', 'path/to/doc2', 'Das ist ein deutsches Dokument.')
    doc1.lang, doc2.lang = "en", "de"
    translate({doc1, doc2}, "de")
    t_mock.assert_called_once()
    assert doc1.text == "Dies ist ein englisches Dokument."


@patch.object(GoogleTranslator, "translate", return_value="Hallo Welt!")
def test_translate_without_lang(t_mock):
    doc = Document('doc', 'path/to/doc', "Hello World!")
    translate({doc}, "de")
    assert doc.text == "Hallo Welt!"


@patch.object(GoogleTranslator, "translate", return_value="Hallo! " * 720)
def test_translate_with_long_doc(t_mock):
    doc = Document('doc', 'path/to/doc', "Hello! " * 720)
    doc.lang = "en"
    translate({doc}, "de")
    assert len(doc.text) > 5000
    assert "Hallo!" in doc.text


@patch("plagdef.model.pipeline.translate._translate")
def test_translate_with_extremely_long_doc(t_mock):
    doc = Document('doc', 'path/to/doc', "Hello Joe!" * 5001)
    doc.lang = "en"
    translate({doc}, "de")
    assert len(doc.text) > 50000
    t_mock.assert_not_called()


@patch("plagdef.model.pipeline.translate._translate")
def test_translate_with_same_source_lang(t_mock):
    doc = Document('doc', 'path/to/doc', "Hello World!")
    doc.lang = "en"
    translate({doc}, "en")
    t_mock.assert_not_called()


def test_split_text_at_punct():
    text = "This is some text. Should be split at dot."
    chunks = _split_text_at_punct(text, 25)
    assert chunks == ['This is some text. ', 'Should be split at dot.']


def test_split_text_at_punct_with_max_len_greater_than_text():
    text = "This is some text. Should not be split at dot."
    chunks = _split_text_at_punct(text, 100)
    assert chunks == ['This is some text. Should not be split at dot.']


def test_split_text_at_punct_with_sent_longer_than_max_len():
    text = "This is some text. Should be split at dot."
    chunks = _split_text_at_punct(text, 10)
    assert chunks == ['This is so', 'me text. ', 'Should be ', 'split at d', 'ot.']
