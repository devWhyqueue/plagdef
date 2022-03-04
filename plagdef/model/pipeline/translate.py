from __future__ import annotations

import logging

from deep_translator import GoogleTranslator
from langdetect import detect
from tqdm import tqdm

from plagdef.model.models import Document

log = logging.getLogger(__name__)


def detect_lang(docs: set[Document]) -> None:
    for doc in docs:
        doc.lang = detect(doc.text) if doc.text else None


def docs_in_other_langs(docs: set[Document], expected_lang: str) -> set[Document]:
    return {doc for doc in docs if doc.lang != expected_lang}


def translate(docs: set[Document], target_lang: str) -> set[Document]:
    translated = set()
    for doc in tqdm(docs, desc='Translating', unit='doc'):
        if doc.lang != target_lang:
            if len(doc.text) < 50000:
                _translate(doc, target_lang)
                translated.add(doc)
            else:
                log.warning(f'Skipping translation of {doc} because its text length is greater than 50k chars.')
    return translated


def _translate(doc: Document, target_lang: str) -> None:
    # The limit of Google Translate Web is less than 5000 chars per request
    chunks = [doc.text[i:i + 4999] for i in range(0, len(doc.text), 4999)]
    for i, chunk in enumerate(chunks):
        chunks[i] = GoogleTranslator(target=target_lang).translate(text=chunk)
    doc.text = "".join(chunks)
