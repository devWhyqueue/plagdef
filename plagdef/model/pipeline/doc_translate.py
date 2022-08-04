import filecmp
import tempfile
from pathlib import Path

import pkg_resources
from PyPDF2 import PdfReader
from fpdf import FPDF
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from unicodedata import normalize
from webdriver_manager.chrome import ChromeDriverManager

from plagdef.model.models import Document

GOOGLE_DOC_TRANSLATE_URL = "https://translate.google.com/?hl=de&sl=auto&tl={TARGET_LANG}&op=docs"


def translate_doc(doc: Document, target_lang: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_file = _save_to_pdf(doc, temp_dir)
        svc = ChromeService(ChromeDriverManager().install())
        with webdriver.Edge(options=_chrome_options(temp_dir), service=svc) as driver:
            _translate_pdf(driver, pdf_file, target_lang)
            if filecmp.cmp(pdf_file, Path(pdf_file).with_suffix(".old")):
                raise TranslationError(f"Could not translate {doc} because Google refused translation.")
            doc.text = _extract_text(pdf_file)
            doc.lang = target_lang


def _save_to_pdf(doc: Document, target_path: str):
    pdf = FPDF()
    font_file = pkg_resources.resource_filename(__name__, str(Path('../../res/DejaVuSansCondensed.ttf')))
    pdf.add_font('DejaVu', fname=font_file)
    pdf.set_font('DejaVu', size=12)
    pdf.add_page()
    pdf.multi_cell(w=0, txt=doc.text)
    file_name = f'{target_path}/{doc.name}.pdf'
    pdf.output(file_name)
    page_num = len(PdfReader(file_name).pages)
    if page_num > 300:
        raise TranslationError(f"Could not translate {doc} because it has more than 300 pages ({page_num}).")
    return file_name


def _chrome_options(default_download_dir: str) -> Options:
    opt = Options()
    opt.add_argument("headless")
    opt.add_argument(
        f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62")
    opt.add_experimental_option("excludeSwitches", ["enable-logging"])
    opt.add_experimental_option("prefs", {
        "download.default_directory": default_download_dir
    })
    opt.add_argument('--disable-blink-features=AutomationControlled')
    return opt


def _translate_pdf(driver: WebDriver, pdf: str, target_lang: str):
    try:
        wait = WebDriverWait(driver, 60)
        driver.get(GOOGLE_DOC_TRANSLATE_URL.replace("{TARGET_LANG}", target_lang))
        driver.find_element(By.XPATH, "//button[@jsname='b3VHJd']").click()
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(pdf)
        translate_button_loc = (By.XPATH, "//button[@jsname='vSSGHe']")
        wait.until(EC.element_to_be_clickable(translate_button_loc))
        driver.find_element(translate_button_loc[0], translate_button_loc[1]).click()
        Path(pdf).rename(Path(pdf).with_suffix(".old"))
        download_button_loc = (By.XPATH, "//button[@jsname='hRZeKc']")
        wait.until(EC.element_to_be_clickable(download_button_loc))
        driver.find_element(download_button_loc[0], download_button_loc[1]).click()
        wait.until(lambda wd: Path(pdf).exists())
    except TimeoutException:
        raise TranslationError(f"Translation request timed out.")


def _extract_text(pdf_file: str) -> str:
    reader = PdfReader(pdf_file)
    text = ' '.join(filter(None, (page.extract_text() for page in reader.pages)))
    text = text.replace("Machine Translated by Google", "")
    return normalize('NFC', text)


class TranslationError(Exception):
    pass
