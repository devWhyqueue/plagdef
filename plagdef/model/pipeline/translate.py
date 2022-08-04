from __future__ import annotations

import concurrent
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from time import sleep

import requests
from deep_translator import GoogleTranslator
from deep_translator.exceptions import RequestError, TooManyRequests
from langdetect import detect
from tqdm import tqdm

from plagdef.model.models import Document
from plagdef.model.pipeline.doc_translate import translate_doc, TranslationError

WEBSHARE_PROXIES = "https://proxy.webshare.io/proxy/list/download/rzeoaimkyxecclzdabargzhwodnrgicaedlyppgc/-/http" \
                   "/username/direct/"

log = logging.getLogger(__name__)


def detect_lang(docs: set[Document]) -> None:
    for doc in docs:
        doc.lang = detect(doc.text) if doc.text else None


def docs_in_other_langs(docs: set[Document], expected_lang: str) -> set[Document]:
    return {doc for doc in docs if doc.lang != expected_lang}


def translate(docs: set[Document], target_lang: str) -> set[Document]:
    proxies = _get_proxies()
    translated = set()
    for doc in tqdm(docs, desc='Translating', unit='doc'):
        if doc.lang != target_lang:
            if len(doc.text) < 50000:
                _translate(doc, target_lang, proxies)
                translated.add(doc)
            else:
                _translate_large_doc(doc, target_lang)
    return translated


def _translate(doc: Document, target_lang: str, proxies: list[str]) -> None:
    # The limit of Google Translate Web is less than 5000 chars per request
    chunks = {(i, chunk) for i, chunk in enumerate(_split_text_at_punct(doc.text, 4999))}
    translated = set()
    while len(chunks) > len(translated):
        chunks = chunks.difference(translated)
        executor = ThreadPoolExecutor(len(proxies))
        futures = [executor.submit(partial(_translate_chunk, target_lang=target_lang,
                                           proxy=proxies[i % len(proxies)]), chunk) for i, chunk in enumerate(chunks)]
        try:
            for future in as_completed(futures, timeout=30):
                result = future.result()
                if result:
                    translated.add(result)
        except concurrent.futures.TimeoutError:
            pass
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    chunk_texts = [chunk[1] for chunk in sorted(translated, key=lambda chunk: chunk[0])]
    doc.text = "".join(chunk_texts)
    doc.lang = target_lang


def _split_text_at_punct(text: str, max_len: int, chunks: list[str] = None) -> list[str]:
    if chunks is None:
        chunks = []
    if len(text) <= max_len:
        return [*chunks, text]
    match = re.search(r'(?s:.*)[\.!\?]\s', text[:max_len])
    chunk = text[:match.end()] if match else text[:max_len]
    chunks.append(chunk)
    return _split_text_at_punct(text[match.end() if match else max_len:], max_len, chunks)


def _translate_chunk(chunk: tuple[int, str], target_lang: str, proxy: str):
    try:
        sleep(1)
        return chunk[0], GoogleTranslator(target=target_lang, proxies={"https": proxy}).translate(text=chunk[1])
    except (RequestError, TooManyRequests):
        return None


def _get_proxies() -> list[str]:
    proxies = []
    for proxy in requests.get(WEBSHARE_PROXIES).text.splitlines():
        address = proxy.split(":")
        proxies.append(f"http://{address[2]}:{address[3]}@{address[0]}:{address[1]}")
    return proxies


def _translate_large_doc(doc: Document, target_lang: str):
    try:
        translate_doc(doc, target_lang)
    except TranslationError as e:
        log.warning(e)
        log.debug('Following error occurred:', exc_info=True)
