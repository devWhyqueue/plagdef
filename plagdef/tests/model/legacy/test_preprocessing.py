import copy
from collections import Counter

from pytest import mark

from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.legacy.preprocessing import LegacyPreprocessor
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import real_docs, doc_factory, config


def test_preprocess_alters_only_vocs_and_offsets_and_bows(doc_factory, config):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document.\n'), \
                 doc_factory.create('doc2', 'This also is a document.\n')
    obj_before = SGSPLAG(doc1.text, doc2.text, config)
    preprocessed_obj = copy.deepcopy(obj_before)
    preprocessor = LegacyPreprocessor()
    preprocessor.preprocess(preprocessed_obj)
    assert (obj_before.src_voc, obj_before.susp_voc) != (preprocessed_obj.src_voc, preprocessed_obj.susp_voc)
    assert (obj_before.src_offsets, obj_before.susp_offsets) != \
           (preprocessed_obj.src_offsets, preprocessed_obj.susp_offsets)
    assert (obj_before.src_bow, obj_before.susp_bow) != (preprocessed_obj.src_bow, preprocessed_obj.susp_bow)
    assert (obj_before.src_text, obj_before.susp_text) == (preprocessed_obj.src_text, preprocessed_obj.susp_text)
    assert obj_before.detections == preprocessed_obj.detections


def test_tokenize_alters_only_vocs_and_offsets(doc_factory, config):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document.\n'), \
                 doc_factory.create('doc2', 'This also is a document.\n')
    obj_before = SGSPLAG(doc1.text, doc2.text, config)
    preprocessed_obj = copy.deepcopy(obj_before)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(preprocessed_obj.src_text, preprocessed_obj.src_voc, preprocessed_obj.src_offsets)
    assert obj_before.src_voc != preprocessed_obj.src_voc
    assert obj_before.src_offsets != preprocessed_obj.src_offsets
    assert obj_before.src_bow == preprocessed_obj.src_bow
    assert obj_before.src_text == preprocessed_obj.src_text
    assert obj_before.detections == preprocessed_obj.detections


@mark.xfail(reason="PyStemmer produces wrong lemmas.")
def test_tokenize_voc_contains_stemmed_tokens_with_sentence_frequency(real_docs, config):
    doc1, doc2 = real_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.src_text, obj.src_voc, obj.src_offsets)
    assert obj.src_voc == Counter(
        {'be': 3, 'infringement': 2, 'the': 2, 'copyright': 2, 'a': 2, 'plagiarism': 1, 'not': 1, 'same': 1, 'as': 1,
         'to': 1, 'concept': 1, 'apply': 1, 'they': 1, 'may': 1, 'while': 1, 'different': 1, 'act': 1, 'particular': 1,
         'term': 1, 'both': 1, 'material': 1, 'consent': 1, 'holder': 1, 'whose': 1, 'violation': 1, 'of': 1, 'use': 1,
         'without': 1, 'restrict': 1, 'when': 1, 'right': 1, 'by': 1})


@mark.xfail(reason="Instead of removing stop words they are not stemmed.")
def test_tokenize_voc_contains_no_stop_words(real_docs, config):
    doc1, doc2 = real_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.src_text, obj.src_voc, obj.src_offsets, 1)
    assert not any(sw in obj.src_voc for sw in
                   ['the', 'of', 'and', 'a', 'in', 'to', 'is', 'was', 'it', 'for', 'with', 'he', 'be', 'on', 'i',
                    'that', 'by', 'at', 'you', '\'s', 'are', 'not', 'his', 'this', 'from', 'but', 'had', 'which',
                    'she', 'they', 'or', 'an', 'were', 'we', 'their', 'been', 'has', 'have', 'will', 'would',
                    'her', 'n\'t', 'there', 'can', 'all', 'as', 'if', 'who', 'what', 'said'])


def test_tokenize_voc_contains_no_short_tokens(real_docs, config):
    doc1, doc2 = real_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.src_text, obj.src_voc, obj.src_offsets)
    assert not any(len(token) < 2 for token in obj.src_voc)


def test_tokenize_offsets(real_docs, config):
    doc1, doc2 = real_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.src_text, obj.src_voc, obj.src_offsets)
    # offset(start_char, length) with start_char + length = end_char (excl.)
    assert obj.src_offsets == [[0, 177], [178, 53], [232, 99]]


def test_tokenize_returns_sent_bows(real_docs, config):
    doc1, doc2 = real_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    sent_bows = preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets)
    assert len(sent_bows) == 3
    # Wrong lemmas ignored
    assert sent_bows == [{'plagiar': 1, 'not': 1, 'the': 1, 'same': 1, 'copyright': 1, 'infring': 1},
                         {'while': 1, 'both': 1, 'term': 1, 'may': 1, 'appli': 1, 'particular': 1, 'act': 1, 'they': 1,
                          'are': 1, 'differ': 1, 'concept': 1},
                         {'copyright': 3, 'infring': 1, 'violat': 1, 'the': 1, 'right': 1, 'holder': 1, 'when': 1,
                          'materi': 1, 'whose': 1, 'use': 2, 'restrict': 1, 'without': 1, 'consent': 1}]


@mark.xfail(reason="Wrong length after join because whitespace is not counted in.")
def test_join_small_sents_offsets(doc_factory, config):
    doc1, doc2 = doc_factory.create('doc1', 'Short sentence. Short sentence should be joined with this one.'), \
                 doc_factory.create('doc2', 'This also is a document.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    sent_bows = preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets)
    preprocessor._join_small_sents(sent_bows, obj.susp_offsets, obj.min_sent_len, obj.susp_voc)
    # First sentence: (0, 15)
    # Second sentence: (16, 46)
    # Combined: (0, 62) because of whitespace gap between sents
    assert obj.susp_offsets == [(0, 62)]


def test_join_small_sents_at_start(doc_factory, config):
    doc1, doc2 = doc_factory.create('doc1', 'Short sentence. Short sentence should be joined with this one.'), \
                 doc_factory.create('doc2', 'This also is a document.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    sent_bows = preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets)
    preprocessor._join_small_sents(sent_bows, obj.susp_offsets, obj.min_sent_len, obj.susp_voc)
    # Wrong lemmas and offsets ignored
    assert len(obj.susp_offsets) == 1
    assert sent_bows == [{'short': 2, 'sentenc': 2, 'should': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1}]
    assert obj.susp_voc == {'short': 1, 'sentenc': 1, 'should': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1}


def test_join_small_sents_in_the_middle(doc_factory, config):
    doc1, doc2 = doc_factory.create('doc1', 'This is a longer sentence. Short sentence. Short sentence should be '
                                            'joined with this one.'), \
                 doc_factory.create('doc2', 'This also is a document.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    sent_bows = preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets)
    preprocessor._join_small_sents(sent_bows, obj.susp_offsets, obj.min_sent_len, obj.susp_voc)
    # Wrong lemmas and offsets ignored
    assert len(obj.susp_offsets) == 2
    assert sent_bows == [{'this': 1, 'longer': 1, 'sentenc': 1},
                         {'short': 2, 'sentenc': 2, 'should': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1}]
    assert obj.susp_voc == {'this': 2, 'longer': 1, 'sentenc': 2, 'short': 1, 'should': 1, 'join': 1, 'with': 1,
                            'one': 1}


@mark.xfail(reason="Short sentences are only joined with next one but last sentence has no successor.")
def test_join_small_sents_at_the_end(doc_factory, config):
    doc1, doc2 = doc_factory.create('doc1', 'This is a longer sentence. Short sentence should be '
                                            'joined with this one. Short sentence.'), \
                 doc_factory.create('doc2', 'This also is a document.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    sent_bows = preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets)
    preprocessor._join_small_sents(sent_bows, obj.susp_offsets, obj.min_sent_len, obj.susp_voc)
    # Wrong lemmas and offsets ignored
    assert len(obj.susp_offsets) == 2


def test_sum_vect(doc_factory, config):
    doc1, doc2 = doc_factory.create('doc1', 'This is a cool document.'), \
                 doc_factory.create('doc2', 'This also is a document.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor.preprocess(obj)
    combined_voc = preprocessor._sum_vect(obj.src_voc, obj.susp_voc)
    assert combined_voc == {'this': 2, 'also': 1, 'document': 2, 'cool': 1}


def test_preprocess_tf_isf(real_docs, config):
    doc1, doc2 = real_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor.preprocess(obj)
    # Example for copyright in third sent:
    # tf-isf = tf x ln(N/sf)
    # tf('copyright') in sent3 = 3
    # N (num of all sents) = 6
    # sf (num of sents containing 'copyright') = 3
    # tf-isf = 3 x ln(6/3) = 2.0794...
    assert obj.susp_bow == [{'plagiar': 0.4054651081081644, 'not': 1.0986122886681098, 'the': 0.1823215567939546,
                             'same': 1.0986122886681098, 'copyright': 0.6931471805599453,
                             'infring': 0.6931471805599453},
                            {'while': 1.791759469228055, 'both': 1.791759469228055, 'term': 1.791759469228055,
                             'may': 1.0986122886681098, 'appli': 1.791759469228055, 'particular': 1.791759469228055,
                             'act': 1.0986122886681098, 'they': 1.791759469228055, 'are': 1.791759469228055,
                             'differ': 1.791759469228055, 'concept': 1.791759469228055},
                            {'copyright': 2.0794415416798357, 'infring': 0.6931471805599453,
                             'violat': 1.791759469228055, 'the': 0.1823215567939546, 'right': 1.791759469228055,
                             'holder': 1.791759469228055, 'when': 1.791759469228055, 'materi': 1.791759469228055,
                             'whose': 1.791759469228055, 'use': 3.58351893845611, 'restrict': 1.791759469228055,
                             'without': 1.791759469228055, 'consent': 1.791759469228055}]
