from __future__ import annotations

import logging
import os
from functools import partial
from mimetypes import guess_extension
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from tqdm.contrib.concurrent import thread_map
from werkzeug.utils import secure_filename

from plagdef.config import settings
from plagdef.model.models import Document, File

log = logging.getLogger(__name__)


def download_all_external_sources(docs: set[Document], target_dir: Path) -> set[File]:
    urls = {url for doc in docs for url in doc.urls}
    files = filter(None, thread_map(partial(_download_page, target_dir=target_dir), urls, max_workers=os.cpu_count(),
                                    total=len(urls), desc='Downloading', unit='external sources'))
    return set(files)


def download_external_sources(doc: Document, target_dir: Path) -> set[File]:
    files = filter(None, thread_map(partial(_download_page, target_dir=target_dir), doc.urls,
                                    max_workers=os.cpu_count(), total=len(doc.urls), desc='Downloading',
                                    unit='external sources'))
    return set(files)


def _download_page(url: str, target_dir: Path) -> File:
    parsed_url = urlparse(url)
    url_path = parsed_url.path.rstrip("/")
    filename = parsed_url.netloc if not url_path else f'{url_path[url_path.rindex("/") + 1:]}_from_{parsed_url.netloc}'
    filename = secure_filename(filename)
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        mime_type = resp.headers['content-type'] if 'content-type' in resp.headers else 'text/html'
        binary = not mime_type.startswith('text')
        content = resp.content if binary else resp.text
        ext = guess_extension(mime_type)
        if mime_type.startswith("text/html"):
            content = BeautifulSoup(resp.text, features="lxml").get_text(" ", True)
            ext = ".txt"
        file = File(Path(f"{target_dir}/{filename}{ext}"), content, binary) \
            if len(content) >= settings['min_ext_size'] else None
        return file
    except RequestException:
        log.debug(f'Could not download from "{url}".')
