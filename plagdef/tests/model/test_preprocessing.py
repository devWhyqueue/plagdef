import copy
from collections import Counter

import pytest

from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.preprocessing import DocumentFactory, UnsupportedLanguageError, Document, Preprocessor
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import real_docs, doc_factory, config


def test_doc_factory_init_lang_models():
    en = DocumentFactory('eng', 3, False)
    de = DocumentFactory('ger', 3, False)
    assert en._nlp_model.lang == 'en'
    assert de._nlp_model.lang == 'de'


def test_doc_factory_init_with_wrong_lang():
    with pytest.raises(UnsupportedLanguageError):
        DocumentFactory('fre', 3, False)


def test_preprocessor_alters_only_vocs_and_offsets_and_bows(doc_factory, config):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document. Short sentence.'), \
                 doc_factory.create('doc2', 'This also is a document. This is longer and this has two sentences.')
    obj_before = SGSPLAG(doc1.text, doc2.text, config)
    preprocessed_obj = copy.deepcopy(obj_before)
    preprocessor = Preprocessor(doc1, doc2)
    preprocessor.preprocess(preprocessed_obj)
    assert (obj_before.src_voc, obj_before.susp_voc) != (preprocessed_obj.src_voc, preprocessed_obj.susp_voc)
    assert (obj_before.src_offsets, obj_before.susp_offsets) != \
           (preprocessed_obj.src_offsets, preprocessed_obj.susp_offsets)
    assert (obj_before.src_bow, obj_before.susp_bow) != (preprocessed_obj.src_bow, preprocessed_obj.susp_bow)
    assert (obj_before.src_text, obj_before.susp_text) == (preprocessed_obj.src_text, preprocessed_obj.susp_text)
    assert obj_before.detections == preprocessed_obj.detections


def test_doc_preprocess_voc_contains_stemmed_tokens_with_sentence_frequency(real_docs):
    doc = real_docs[0]
    assert doc.vocab == Counter(
        {'be': 3, 'infringement': 2, 'the': 2, 'copyright': 2, 'a': 2, 'plagiarism': 1, 'not': 1, 'same': 1, 'as': 1,
         'to': 1, 'concept': 1, 'apply': 1, 'they': 1, 'may': 1, 'while': 1, 'different': 1, 'act': 1, 'particular': 1,
         'term': 1, 'both': 1, 'material': 1, 'consent': 1, 'holder': 1, 'whose': 1, 'violation': 1, 'of': 1, 'use': 1,
         'without': 1, 'restrict': 1, 'when': 1, 'right': 1, 'by': 1})


def test_doc_preprocess_voc_contains_no_stop_words():
    doc_factory = DocumentFactory('eng', 3, True)
    doc = doc_factory.create('doc1', 'This is a sentence with five stop words.')
    assert len(doc.vocab.keys()) == 3


def test_doc_preprocess_voc_contains_short_tokens(real_docs, config):
    doc = real_docs[0]
    assert any(len(token) < 2 for token in doc.vocab)


def test_doc_preprocess_sent_start_end_chars(real_docs):
    doc = real_docs[1]
    assert [(sent.start_char, sent.end_char) for sent in doc.sents] == [(0, 177), (178, 231), (232, 331)]


def test_doc_preprocess_sent_start_end_chars_after_join(doc_factory):
    doc = doc_factory.create('doc1', 'Short sentence. Short sentence should be joined with this one.')
    # First sentence: (0, 15)
    # Second sentence: (16, 46)
    # Combined: (0, 62) because of whitespace gap between sents
    assert len(doc.sents) == 1
    assert (doc.sents[0].start_char, doc.sents[0].end_char) == (0, 62)


def test_doc_preprocess_sent_bows(real_docs):
    doc = real_docs[0]
    assert [sent.bow for sent in doc.sents] == [
        Counter({'plagiarism': 1, 'be': 1, 'not': 1, 'the': 1, 'same': 1, 'as': 1, 'copyright': 1, 'infringement': 1}),
        Counter({'while': 1, 'both': 1, 'term': 1, 'may': 1, 'apply': 1, 'to': 1, 'a': 1, 'particular': 1, 'act': 1,
                 'they': 1, 'be': 1, 'different': 1, 'concept': 1}),
        Counter({'copyright': 3, 'be': 3, 'a': 2, 'of': 2, 'use': 2, 'infringement': 1, 'violation': 1, 'the': 1,
                 'right': 1, 'holder': 1, 'when': 1, 'material': 1, 'whose': 1, 'restrict': 1, 'by': 1, 'without': 1,
                 'consent': 1})]


def test_doc_join_small_sents_at_start(doc_factory):
    doc = doc_factory.create('doc1', 'Short sentence. Short sentence should be joined with this one.')
    assert len(doc.sents) == 1
    assert [sent.bow for sent in doc.sents] == \
           [Counter({'short': 2, 'sentence': 2, 'should': 1, 'be': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1})]
    assert doc.vocab == Counter(
        {'sentence': 1, 'short': 1, 'this': 1, 'should': 1, 'one': 1, 'be': 1, 'with': 1, 'join': 1})


def test_doc_join_small_sents_in_the_middle(doc_factory):
    doc = doc_factory.create('doc1', 'This is a longer sentence. Short sentence. Short sentence should be '
                                     'joined with this one.')
    assert len(doc.sents) == 2
    assert [sent.bow for sent in doc.sents] == \
           [Counter({'this': 1, 'be': 1, 'a': 1, 'long': 1, 'sentence': 1}),
            Counter({'short': 2, 'sentence': 2, 'should': 1, 'be': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1})]
    assert doc.vocab == Counter(
        {'be': 2, 'sentence': 2, 'this': 2, 'a': 1, 'long': 1, 'short': 1, 'one': 1, 'join': 1, 'with': 1, 'should': 1})


def test_doc_join_small_sents_at_the_end(doc_factory):
    doc = doc_factory.create('doc1', 'This is a longer sentence. Short sentence should be '
                                     'joined with this one. Short sentence.')
    assert len(doc.sents) == 2
    assert [sent.bow for sent in doc.sents] == \
           [Counter({'this': 1, 'be': 1, 'a': 1, 'long': 1, 'sentence': 1}),
            Counter({'short': 2, 'sentence': 2, 'should': 1, 'be': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1})]
    assert doc.vocab == Counter(
        {'be': 2, 'sentence': 2, 'this': 2, 'a': 1, 'long': 1, 'short': 1, 'one': 1, 'join': 1, 'with': 1, 'should': 1})


def test_doc_preprocess_tf_isf(real_docs, config):
    doc1, doc2 = real_docs
    Document.update_sent_bows_with_tf_isf(doc1, doc2)
    # Example for copyright in third sent:
    # tf-isf = tf x ln(N/sf)
    # tf('copyright') in sent3 = 3
    # N (num of all sents) = 6
    # sf (num of sents containing 'copyright') = 3
    # tf-isf = 3 x ln(6/3) = 2.0794...
    assert [sent.bow for sent in doc1.sents] == \
           [Counter({'not': 1.0986122886681098, 'same': 1.0986122886681098, 'as': 1.0986122886681098,
                     'copyright': 0.6931471805599453, 'infringement': 0.6931471805599453,
                     'plagiarism': 0.4054651081081644, 'be': 0.1823215567939546, 'the': 0.1823215567939546}),
            Counter({'while': 1.791759469228055, 'both': 1.791759469228055, 'term': 1.791759469228055,
                     'apply': 1.791759469228055, 'particular': 1.791759469228055, 'they': 1.791759469228055,
                     'different': 1.791759469228055, 'concept': 1.791759469228055, 'may': 1.0986122886681098,
                     'to': 1.0986122886681098, 'act': 1.0986122886681098, 'a': 0.4054651081081644,
                     'be': 0.1823215567939546}),
            Counter({'use': 3.58351893845611, 'of': 2.1972245773362196, 'copyright': 2.0794415416798357,
                     'violation': 1.791759469228055, 'right': 1.791759469228055, 'holder': 1.791759469228055,
                     'when': 1.791759469228055, 'material': 1.791759469228055, 'whose': 1.791759469228055,
                     'restrict': 1.791759469228055, 'by': 1.791759469228055, 'without': 1.791759469228055,
                     'consent': 1.791759469228055, 'a': 0.8109302162163288, 'infringement': 0.6931471805599453,
                     'be': 0.5469646703818638, 'the': 0.1823215567939546})]
