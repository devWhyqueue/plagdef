from __future__ import annotations

import io
import math
from collections import Counter
from dataclasses import dataclass

import spacy
from more_itertools import pairwise
from somajo import SoMaJo
from spacy import Language


class Preprocessor:
    def __init__(self, lang: str, min_sent_len: int, rem_stop_words: bool):
        self._min_sent_len = min_sent_len
        self._rem_stop_words = rem_stop_words
        if lang == 'eng':
            self._nlp_model = spacy.load('en_core_web_trf')
        elif lang == 'ger':
            self._nlp_model = spacy.load('de_core_news_sm')
            self._nlp_model.add_pipe("ger_sent_seg", before="parser")
        else:
            raise UnsupportedLanguageError(f'The language "{lang}" is currently not supported.')

    # TODO: Only for compatibility
    def set_docs(self, doc1: Document, doc2: Document):
        self._doc1 = doc1
        self._doc2 = doc2

    # TODO: Only for compatibility
    def preprocess(self, legacy_obj):
        self.preprocess_doc_pair(self._doc1, self._doc2)
        legacy_obj.susp_voc = self._doc1.vocab
        legacy_obj.susp_bow = [sent.bow_tf_isf for sent in self._doc1.sents]
        legacy_obj.susp_offsets = [(sent.start_char, sent.end_char - sent.start_char) for sent in self._doc1.sents]
        legacy_obj.src_voc = self._doc2.vocab
        legacy_obj.src_bow = [sent.bow_tf_isf for sent in self._doc2.sents]
        legacy_obj.src_offsets = [(sent.start_char, sent.end_char - sent.start_char) for sent in self._doc2.sents]

    # TODO: New single preprocess
    def preprocess_new(self, docs: list[Document]):
        parsed_docs = self._nlp_model.pipe([doc.text for doc in docs])
        for idx, parsed_doc in enumerate(parsed_docs):
            for sent in parsed_doc.sents:
                if self._rem_stop_words:
                    sent_lemmas = [token.lemma_.lower() for token in sent if token.text.isalnum() and not token.is_stop]
                else:
                    sent_lemmas = [token.lemma_.lower() for token in sent if token.text.isalnum()]
                if len(sent_lemmas):
                    lemma_count = Counter(sent_lemmas)
                    docs[idx].sents.append(Sentence(docs[idx], sent.start_char, sent.end_char, lemma_count, {}))
                    for lemma in lemma_count.keys():
                        docs[idx].vocab[lemma] += 1

            self._join_small_sentences(docs[idx])

    # TODO: New pair preprocess function
    def preprocess_doc_pair(self, doc1: Document, doc2: Document):
        """
        Compute the tf-isf = tf x ln(N/sf), N being the number of sentences in corpus
        and sf the number of sentences containing the term
        """
        sf = doc1.vocab + doc2.vocab
        N = len(doc1.sents) + len(doc2.sents)
        for sent in doc1.sents:
            for lemma in sent.bow:
                sent.bow_tf_isf[lemma] = sent.bow[lemma] * math.log(N / float(sf[lemma]))
        for sent in doc2.sents:
            for lemma in sent.bow:
                sent.bow_tf_isf[lemma] = sent.bow[lemma] * math.log(N / float(sf[lemma]))

    def _join_small_sentences(self, doc: Document):
        for sent1, sent2 in pairwise(doc.sents):
            if sum(sent1.bow.values()) < self._min_sent_len or (
                sent2 == doc.sents[-1] and sum(sent2.bow.values()) < self._min_sent_len):
                for lemma in sent1.bow.keys():
                    if lemma in sent2.bow:
                        doc.vocab[lemma] -= 1
                sent2.bow.update(sent1.bow)
                sent2.start_char = sent1.start_char
                doc.sents.remove(sent1)


class Document:
    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text
        self.vocab = Counter()  # <lemma, sent_freq>
        self.sents: list[Sentence] = []

    def __eq__(self, other):
        return isinstance(other, Document) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


@dataclass
class Sentence:
    doc: Document
    start_char: int
    end_char: int
    bow: Counter
    bow_tf_isf: dict


class UnsupportedLanguageError(Exception):
    pass


@Language.component("ger_sent_seg")
def ger_sent_seg(spacy_doc):
    _unmark_all_spacy_tokens(spacy_doc)
    somajo_sent_starts = _find_somajo_sent_starts(spacy_doc.text)
    _find_and_mark_spacy_tokens(spacy_doc, somajo_sent_starts)
    return spacy_doc


def _unmark_all_spacy_tokens(spacy_doc):
    for token in spacy_doc[:-1]:
        spacy_doc[token.i].is_sent_start = False


def _find_somajo_sent_starts(doc_text: str) -> list[int]:
    tokenizer = SoMaJo("de_CMC")
    somajo_sents = tokenizer.tokenize_text_file(io.StringIO(doc_text), paragraph_separator="empty_lines")
    somajo_start_idx = 0
    somajo_sent_starts = []
    for sent in somajo_sents:
        for token in sent:
            token_text = token.original_spelling if token.original_spelling else token.text
            token_text_idx = doc_text[somajo_start_idx:].find(token_text) + somajo_start_idx
            if token.first_in_sentence:
                somajo_sent_starts.append(token_text_idx)
            somajo_start_idx = token_text_idx + len(token_text)
    return somajo_sent_starts


def _find_and_mark_spacy_tokens(spacy_doc, somajo_sent_starts):
    spacy_last_token_i = 0
    for somajo_start_idx in somajo_sent_starts:
        spacy_last_token_i = _mark_spacy_token_by_char(spacy_doc, spacy_last_token_i, somajo_start_idx) + 1


def _mark_spacy_token_by_char(spacy_doc, spacy_start_token_i, char_idx) -> int:
    for spacy_token in spacy_doc[spacy_start_token_i:]:
        if char_idx > spacy_token.idx:
            continue
        if char_idx == spacy_token.idx:
            spacy_doc[spacy_token.i].is_sent_start = True
            return spacy_token.i
        if char_idx < spacy_token.idx:
            spacy_doc[spacy_token.i - 1].is_sent_start = True
            return spacy_token.i - 1
