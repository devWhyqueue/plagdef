from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

import spacy
from more_itertools import pairwise
from spacy import Language


# TODO: Only for backwards compatibility
class Preprocessor:
    def __init__(self, doc1: Document, doc2: Document):
        self._doc1 = doc1
        self._doc2 = doc2

    def preprocess(self, legacy_obj):
        legacy_obj.susp_voc = self._doc1.vocab
        legacy_obj.susp_bow = [sent.bow for sent in self._doc1.sents]
        legacy_obj.susp_offsets = [(sent.start_char, sent.end_char - sent.start_char) for sent in self._doc1.sents]
        legacy_obj.src_voc = self._doc2.vocab
        legacy_obj.src_bow = [sent.bow for sent in self._doc2.sents]
        legacy_obj.src_offsets = [(sent.start_char, sent.end_char - sent.start_char) for sent in self._doc2.sents]


class DocumentFactory:
    def __init__(self, lang: str, min_sent_len: int, rem_stop_words: bool):
        self._min_sent_len = min_sent_len
        self._rem_stop_words = rem_stop_words
        if lang == 'eng':
            self._nlp_model = spacy.load('en_core_web_sm')
        elif lang == 'ger':
            self._nlp_model = spacy.load('de_core_news_sm')
        else:
            raise UnsupportedLanguageError(f'The language "{lang}" is currently not supported.')

    def create(self, name, text) -> Document:
        return Document(name, text, self._min_sent_len, self._rem_stop_words, self._nlp_model)


class Document:
    @classmethod
    def update_sent_bows_with_tf_isf(cls, doc1: Document, doc2: Document):
        """
        Compute the tf-isf = tf x ln(N/sf), N being the number of sentences in corpus
        and sf the number of sentences containing the term
        """
        sf = doc1.vocab + doc2.vocab
        N = len(doc1.sents) + len(doc2.sents)
        for sent in doc1.sents:
            for lemma in sent.bow:
                sent.bow[lemma] *= math.log(N / float(sf[lemma]))
        for sent in doc2.sents:
            for lemma in sent.bow:
                sent.bow[lemma] *= math.log(N / float(sf[lemma]))

    def __init__(self, name: str, text: str, min_sent_len: int, rem_stop_words: bool, nlp_model: Language):
        self.name = name
        self.text = text
        self.vocab = Counter()  # <lemma, sent_freq>
        self.sents: list[Sentence] = []
        self._min_sent_len = min_sent_len
        self._rem_stop_words = rem_stop_words
        self._preprocess(nlp_model)

    def _preprocess(self, nlp_model: Language):
        stop_words = nlp_model.Defaults.stop_words
        parsed_doc = nlp_model(self.text)

        for sent in parsed_doc.sents:
            if self._rem_stop_words:
                sent_lemmas = [token.lemma_ for token in sent if (token.is_alpha or token.is_digit)
                               and token.lower_ not in stop_words]
            else:
                sent_lemmas = [token.lemma_ for token in sent if token.is_alpha or token.is_digit]

            self.sents.append(Sentence(self, sent.start_char, sent.end_char, Counter(sent_lemmas)))
            for lemma in set(sent_lemmas):
                self.vocab[lemma] += 1

        self._join_small_sentences()

    def _join_small_sentences(self):
        for sent1, sent2 in pairwise(self.sents):
            if sum(sent1.bow.values()) < self._min_sent_len or (
                sent2 == self.sents[-1] and sum(sent2.bow.values()) < self._min_sent_len):
                for lemma in sent1.bow.keys():
                    if lemma in sent2.bow:
                        self.vocab[lemma] -= 1
                sent2.bow.update(sent1.bow)
                sent2.start_char = sent1.start_char
                self.sents.remove(sent1)

    def __eq__(self, other):
        return isinstance(other, Document) and self.name == other.name and self.text == other.text

    def __hash__(self):
        return hash((self.name, self.text))


@dataclass
class Sentence:
    doc: Document
    start_char: int
    end_char: int
    bow: Counter


class UnsupportedLanguageError(Exception):
    pass
