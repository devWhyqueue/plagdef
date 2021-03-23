import copy

from pytest import mark

from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.legacy.preprocessing import LegacyPreprocessor
from plagdef.model.preprocessing import Document


def test_preprocess_alters_only_vocs_and_offsets_and_bows(config):
    doc1, doc2 = Document('doc1', 'This is a document.\n'), \
                 Document('doc2', 'This also is a document.\n')
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


def test_tokenize_alters_only_vocs_and_offsets(config):
    doc1, doc2 = Document('doc1', 'This is a document.\n'), \
                 Document('doc2', 'This also is a document.\n')
    obj_before = SGSPLAG(doc1.text, doc2.text, config)
    preprocessed_obj = copy.deepcopy(obj_before)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(preprocessed_obj.src_text, preprocessed_obj.src_voc, preprocessed_obj.src_offsets)
    assert obj_before.src_voc != preprocessed_obj.src_voc
    assert obj_before.src_offsets != preprocessed_obj.src_offsets
    assert obj_before.src_bow == preprocessed_obj.src_bow
    assert obj_before.src_text == preprocessed_obj.src_text
    assert obj_before.detections == preprocessed_obj.detections


@mark.xfail(reason="PyStemmer produces wrong stems.")
def test_tokenize_voc_contains_stemmed_tokens_with_sentence_frequency(preprocessed_docs, config):
    doc1, doc2 = preprocessed_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets)
    # Errors: plagiar (plagiari), materi (material), holder (hold)
    assert obj.susp_voc == {'plagiari': 1, 'not': 1, 'the': 2, 'same': 1, 'copyright': 2, 'infring': 2, 'while': 1,
                            'both': 1, 'term': 1, 'may': 1, 'appli': 1, 'particular': 1, 'act': 1, 'they': 1, 'are': 1,
                            'differ': 1, 'concept': 1, 'violat': 1, 'right': 1, 'hold': 1, 'when': 1, 'material': 1,
                            'whose': 1, 'use': 1, 'restrict': 1, 'without': 1, 'consent': 1}


@mark.xfail(reason="PyStemmer produces wrong German stems.")
def test_tokenize_voc_contains_stemmed_german_tokens(config):
    doc1 = Document('doc',
                    'Als Wortstamm oder kurz Stamm bezeichnet man in der '
                    'Grammatik einen Bestandteil eines Wortes, der als '
                    'Ausgangsbasis für weitere Wortbildung dienen kann. '
                    'Es handelt sich demnach um ein potenziell '
                    'unvollständiges Gebilde, das als Gegenstück zu '
                    'einem Affix auftreten kann.')
    doc2 = Document('doc2', 'Ein zweites Dokument der Vollständigkeit halber.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets)
    # Errors:
    # al (als), bezeichnet (bezeichne), einen (ein), ausgangsbasi (ausgangsbasis),
    # dienen (dien), handelt (handel), potenziel (potenz), einem (ein),
    # auftreten (auftr)
    assert list(obj.susp_voc.keys()) \
           == ['als', 'wortstamm', 'oder', 'kurz', 'stamm', 'bezeichne', 'man',
               'der', 'grammatik', 'ein', 'bestandteil', 'wort', 'ausgangsbasis',
               'für', 'weiter', 'wortbildung', 'dien', 'kann', 'handel', 'sich',
               'demnach', 'potenz', 'unvollständig', 'gebild', 'das',
               'gegenstück', 'affix', 'auftr']


@mark.xfail(reason="Instead of removing stop words they are not stemmed.")
def test_preprocessed_voc_contains_no_stop_words(config):
    doc1 = Document('doc1', 'This sentence has five stop words '
                            'which are not removed.')
    doc2 = Document('doc2', 'Another document for good measure.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets, 1)
    assert len(obj.susp_voc.keys()) == 5  # actual: 10
    assert not any(token in obj.susp_voc for
                   token in ['this', 'has', 'which', 'are', 'not'])  # actual: True


def test_tokenize_voc_contains_no_short_tokens(preprocessed_docs, config):
    doc1, doc2 = preprocessed_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.src_text, obj.src_voc, obj.src_offsets)
    assert not any(len(token) < 2 for token in obj.src_voc)


def test_tokenize_offsets(preprocessed_docs, config):
    doc1, doc2 = preprocessed_docs
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor._tokenize(obj.src_text, obj.src_voc, obj.src_offsets)
    # offset(start_char, length) with start_char + length = end_char (excl.)
    assert obj.src_offsets == [[0, 177], [178, 53], [232, 99]]


def test_tokenize_returns_sent_bows(preprocessed_docs, config):
    doc1, doc2 = preprocessed_docs
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


@mark.xfail(reason="Wrong length after join because whitespace "
                   "is not counted in.")
def test_join_small_sents_offsets(config):
    doc1 = Document('doc1', 'Short sentence. Short sentence '
                            'should be joined with this one.')
    doc2 = Document('doc2', 'Another document for good measure')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    sent_bows = preprocessor._tokenize(obj.susp_text, obj.susp_voc,
                                       obj.susp_offsets)
    preprocessor._join_small_sents(sent_bows, obj.susp_offsets,
                                   obj.min_sent_len, obj.susp_voc)
    # First sentence: (0, 15)
    # Second sentence: (16, 46)
    # Combined: (0, 62) because of whitespace gap between sentences
    assert obj.susp_offsets == [(0, 62)]  # actual: [(0, 61)]


def test_join_small_sents_at_start(config):
    doc1, doc2 = Document('doc1', 'Short sentence. Short sentence should be joined with this one.'), \
                 Document('doc2', 'This also is a document.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    sent_bows = preprocessor._tokenize(obj.susp_text, obj.susp_voc, obj.susp_offsets)
    preprocessor._join_small_sents(sent_bows, obj.susp_offsets, obj.min_sent_len, obj.susp_voc)
    # Wrong lemmas and offsets ignored
    assert len(obj.susp_offsets) == 1
    assert sent_bows == [{'short': 2, 'sentenc': 2, 'should': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1}]
    assert obj.susp_voc == {'short': 1, 'sentenc': 1, 'should': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1}


def test_join_small_sents_in_the_middle(config):
    doc1, doc2 = Document('doc1', 'This is a longer sentence. Short sentence. Short sentence should be '
                                  'joined with this one.'), \
                 Document('doc2', 'This also is a document.')
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


@mark.xfail(reason="Short sentences are only joined with next one "
                   "but last sentence has no successor.")
def test_join_small_sents_at_the_end(config):
    doc1 = Document('doc1', 'This is a longer sentence. Short sentence '
                            'should be joined with this one. '
                            'Short sentence.')
    doc2 = Document('doc2', 'Another document for good measure.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    sent_bows = preprocessor._tokenize(obj.susp_text, obj.susp_voc,
                                       obj.susp_offsets)
    preprocessor._join_small_sents(sent_bows, obj.susp_offsets,
                                   obj.min_sent_len, obj.susp_voc)
    assert len(obj.susp_offsets) == 2  # actual: 3


def test_sum_vect(config):
    doc1, doc2 = Document('doc1', 'This is a cool document.'), \
                 Document('doc2', 'This also is a document.')
    obj = SGSPLAG(doc1.text, doc2.text, config)
    preprocessor = LegacyPreprocessor()
    preprocessor.preprocess(obj)
    combined_voc = preprocessor._sum_vect(obj.src_voc, obj.susp_voc)
    assert combined_voc == {'this': 2, 'also': 1, 'document': 2, 'cool': 1}


def test_preprocess_tf_isf(preprocessed_docs, config):
    doc1, doc2 = preprocessed_docs
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
