from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

import stanza
from more_itertools import pairwise

from plagdef.model import stopwords


class Preprocessor:
    def __init__(self, lang: str, min_sent_len: int, rem_stop_words: bool):
        self._lang = lang
        self._min_sent_len = min_sent_len
        self._rem_stop_words = rem_stop_words
        if lang == 'eng':
            try:
                self._nlp_model = stanza.Pipeline('en', processors='tokenize,mwt,pos,lemma', logging_level='WARN')
            except:  # Unpickling error raises Exception, cannot narrow
                stanza.download('en', processors='tokenize,mwt,pos,lemma', logging_level='INFO')
                self._nlp_model = stanza.Pipeline('en', processors='tokenize,mwt,pos,lemma', logging_level='WARN')
        elif lang == 'ger':
            try:
                self._nlp_model = stanza.Pipeline('de', processors='tokenize,mwt,pos,lemma', logging_level='WARN')
            except:  # Unpickling error raises Exception, cannot narrow
                stanza.download('de', processors='tokenize,mwt,pos,lemma', logging_level='INFO')
                self._nlp_model = stanza.Pipeline('de', processors='tokenize,mwt,pos,lemma', logging_level='WARN')
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
        parsed_docs = self._nlp_model([stanza.Document([], text=doc.text) for doc in docs]) if docs else []
        stop_words = stopwords.ENGLISH if self._lang == 'eng' else stopwords.GERMAN
        for doc_idx, parsed_doc in enumerate(parsed_docs):
            for sent in parsed_doc.sentences:
                if self._rem_stop_words:
                    sent_lemmas = [word.lemma for word in sent.words
                                   if not word.upos == 'PUNCT' and word.text.lower() not in stop_words]
                else:
                    sent_lemmas = [word.lemma for word in sent.words if not word.upos == 'PUNCT']
                if len(sent_lemmas):
                    lemma_count = Counter(sent_lemmas)
                    docs[doc_idx].sents.append(
                        Sentence(docs[doc_idx], sent.tokens[0].start_char, sent.tokens[-1].end_char, lemma_count, {}))
                    for lemma in lemma_count.keys():
                        docs[doc_idx].vocab[lemma] += 1

            self._join_small_sentences(docs[doc_idx])

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
