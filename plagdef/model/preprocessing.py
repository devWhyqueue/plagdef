from __future__ import annotations

from collections import Counter

import stanza
from stanza import Pipeline

from plagdef.model import stopwords
from plagdef.model.models import Document, Sentence, Word

PRCS = 'tokenize,mwt,pos,lemma'
PIPE_LVL = 'WARN'
LOAD_LVL = 'INFO'
LANG_CODES = {'ger': 'de', 'eng': 'en'}


class Preprocessor:
    def __init__(self, min_sent_len: int, rem_stop_words: bool):
        self._min_sent_len = min_sent_len
        self._rem_stop_words = rem_stop_words

    def preprocess(self, lang: str, docs: list[Document], common_docs: list[Document] = None):
        if common_docs:
            self.preprocess(lang, common_docs)
        nlp_model = _nlp_pipe(lang)
        parsed_docs = nlp_model([stanza.Document([], text=doc.text) for doc in docs]) if docs else []
        stop_words = stopwords.ENGLISH if lang == 'eng' else stopwords.GERMAN
        common_sent_words = [sent.words for doc_sents in (doc.sents for doc in common_docs)
                             for sent in doc_sents] if common_docs else []
        for doc_idx, parsed_doc in enumerate(parsed_docs):
            for sent_idx, sent in enumerate(parsed_doc.sentences):
                non_punct_words = [word for word in sent.words if not word.upos == 'PUNCT']
                if self._rem_stop_words:
                    sent_lemmas = [word.lemma for word in non_punct_words if word.text.lower() not in stop_words]
                else:
                    sent_lemmas = [word.lemma for word in non_punct_words]
                if len(sent_lemmas):
                    lemma_count = Counter(sent_lemmas)
                    sentence = Sentence(sent.tokens[0].start_char, sent.tokens[-1].end_char, lemma_count, docs[doc_idx])
                    sentence.words = _to_words(sent.tokens, sentence)
                    if not _sent_contains_words_of_common_sent(sentence.words, common_sent_words):
                        docs[doc_idx].sents.add(sentence)
                        for lemma in lemma_count.keys():
                            docs[doc_idx].vocab[lemma] += 1
            self._join_small_sentences(docs[doc_idx])

    def _join_small_sentences(self, doc: Document):
        idx, sent_count = 0, len(doc.sents)
        while idx < sent_count - 1:
            sent1, sent2 = doc.sents[idx], doc.sents[idx + 1]
            if sum(sent1.bow.values()) < self._min_sent_len \
                or (sent2 == doc.sents[-1] and sum(sent2.bow.values()) < self._min_sent_len):
                for lemma in sent1.bow.keys():
                    if lemma in sent2.bow:
                        doc.vocab[lemma] -= 1
                joined_sent = Sentence(sent1.start_char, sent2.end_char, sent1.bow + sent2.bow, doc)
                joined_sent.words = sent1.words + sent2.words
                doc.sents.remove(sent1), doc.sents.remove(sent2)
                doc.sents.add(joined_sent)
                sent_count -= 1
            idx += 1


def _nlp_pipe(lang: str) -> Pipeline:
    if lang in LANG_CODES:
        try:
            return stanza.Pipeline(LANG_CODES[lang], processors=PRCS, logging_level=PIPE_LVL)
        except:  # Unpickling error raises Exception, cannot narrow
            stanza.download(LANG_CODES[lang], processors=PRCS, logging_level=LOAD_LVL)
            return stanza.Pipeline(LANG_CODES[lang], processors=PRCS, logging_level=PIPE_LVL)
    else:
        raise UnsupportedLanguageError(f'The language "{lang}" is currently not supported.')


def _to_words(stanza_tokens, sentence: Sentence) -> list[Word]:
    words = []
    for stanza_token in stanza_tokens:
        for stanza_word in stanza_token.words:
            if not stanza_word.upos == 'PUNCT':
                words.append(Word(stanza_token.start_char, stanza_token.end_char, sentence))
    return words


def _sent_contains_words_of_common_sent(sent_words: list[Word], common_sent_words: list[list[Word]]) -> bool:
    sent_word_texts = [word.text for word in sent_words]
    for sent_words in common_sent_words:
        if all(word.text in sent_word_texts for word in sent_words):
            return True
    return False


class UnsupportedLanguageError(Exception):
    pass
