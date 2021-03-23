import copy
from collections import Counter

import pytest

from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.preprocessing import UnsupportedLanguageError, Document, Preprocessor


def test_preprocessor_init_lang_models():
    en = Preprocessor('eng', 3, False)
    de = Preprocessor('ger', 3, False)
    assert en._nlp_model.lang == 'en'
    assert de._nlp_model.lang == 'de'


def test_preprocessor_init_with_wrong_lang():
    with pytest.raises(UnsupportedLanguageError):
        Preprocessor('fre', 3, False)


def test_ger_sent_seg(nlp_ger):
    doc = nlp_ger('Das ist ein schöner deutscher Text. Besteht aus zwei Sätzen.')
    sent1_words, sent2_words = doc.sentences[0].words, doc.sentences[1].words
    assert len(doc.sentences) == 2
    assert sent1_words[0].text == 'Das' and sent2_words[0].text == 'Besteht'


def test_ger_sent_seg_with_same_sent_starts(nlp_ger):
    doc = nlp_ger('Das ist ein schöner deutscher Text. Das ist auch einer.')
    sent1_tokens, sent2_tokens = doc.sentences[0].tokens, doc.sentences[1].tokens
    assert len(doc.sentences) == 2
    assert sent1_tokens[0].text == 'Das' and sent2_tokens[0].text == 'Das'
    assert sent1_tokens[0].start_char != sent2_tokens[0].start_char


def test_ger_sent_seg_with_next_sent_start_in_previous_sent(nlp_ger):
    doc = nlp_ger('Eine Klasse besteht aus Methoden und Attributen. Methoden realisieren Verhalten.')
    sent1_tokens, sent2_tokens = doc.sentences[0].tokens, doc.sentences[1].tokens
    assert len(doc.sentences) == 2
    assert sent1_tokens[0].text == 'Eine' and sent2_tokens[0].text == 'Methoden'
    assert sent1_tokens[0].start_char == 0 and sent2_tokens[0].start_char == 49


def test_ger_sent_seg_with_paragraphs(nlp_ger):
    doc = nlp_ger('Ein schöner deutscher Text\n\nKurzer Satz.\nUnd noch ein etwas längerer.')
    sent1_words, sent2_words, sent3_words = doc.sentences[0].words, doc.sentences[1].words, doc.sentences[2].words
    assert len(doc.sentences) == 3
    assert sent1_words[0].text == 'Ein' and sent2_words[0].text == 'Kurzer' and sent3_words[0].text == 'Und'


def test_preprocess_alters_only_vocs_and_offsets_and_bows(preprocessor_eng, config):
    doc1, doc2 = Document('doc1', 'This is a document. Short sentence.'), \
                 Document('doc2', 'This also is a document. This is longer and this has two sentences.')
    obj_before = SGSPLAG(doc1.text, doc2.text, config)
    preprocessed_obj = copy.deepcopy(obj_before)
    preprocessor_eng.preprocess_new([doc1, doc2])
    preprocessor_eng.set_docs(doc1, doc2)
    preprocessor_eng.preprocess(preprocessed_obj)
    assert (obj_before.src_voc, obj_before.susp_voc) != (preprocessed_obj.src_voc, preprocessed_obj.susp_voc)
    assert (obj_before.src_offsets, obj_before.susp_offsets) != \
           (preprocessed_obj.src_offsets, preprocessed_obj.susp_offsets)
    assert (obj_before.src_bow, obj_before.susp_bow) != (preprocessed_obj.src_bow, preprocessed_obj.susp_bow)
    assert (obj_before.src_text, obj_before.susp_text) == (preprocessed_obj.src_text, preprocessed_obj.susp_text)
    assert obj_before.detections == preprocessed_obj.detections


def test_preprocessed_voc_contains_lemmas_with_sentence_frequency(preprocessed_docs):
    doc = preprocessed_docs[0]
    # One error (ignored): rights -> right
    assert doc.vocab == Counter(
        {'be': 3, 'infringement': 2, 'the': 2, 'copyright': 2, 'a': 2, 'plagiarism': 1, 'not': 1, 'same': 1, 'as': 1,
         'to': 1, 'concept': 1, 'apply': 1, 'they': 1, 'may': 1, 'while': 1, 'different': 1, 'act': 1, 'particular': 1,
         'term': 1, 'both': 1, 'material': 1, 'consent': 1, 'holder': 1, 'whose': 1, 'violation': 1, 'of': 1, 'use': 1,
         'without': 1, 'restrict': 1, 'when': 1, 'rights': 1, 'by': 1})


def test_tokenize_voc_contains_german_lemmas(preprocessor_ger):
    doc = Document('doc',
                   'Als Wortstamm oder kurz Stamm bezeichnet man in der Grammatik '
                   'einen Bestandteil eines Wortes, der als Ausgangsbasis für '
                   'weitere Wortbildung dienen kann. Es handelt sich demnach um '
                   'ein potenziell unvollständiges Gebilde, das als Gegenstück zu '
                   'einem Affix auftreten kann.')
    preprocessor_ger.preprocess_new([doc])
    # Errors (ignored):
    # Term 'sich' is mapped to 'er|sie|es' but not 'es'
    # Either map all (reflexive) pronouns to 'er|es|sie' or none
    assert list(doc.vocab.keys()) \
           == ['als', 'Wortstamm', 'oder', 'kurz', 'Stamm', 'bezeichnen', 'man',
               'in', 'der', 'Grammatik', 'ein', 'Bestandteil', 'Wort',
               'Ausgangsbasis', 'für', 'weit', 'Wortbildung', 'dienen', 'können',
               'es', 'handeln', 'er|es|sie', 'demnach', 'um', 'potenziell',
               'unvollständig', 'Gebilde', 'Gegenstück', 'zu', 'Affix',
               'auftreten']


def test_preprocessed_voc_contains_no_stop_words():
    preprocessor = Preprocessor('eng', 3, True)
    doc1 = Document('doc1', 'This is a sentence with five stop words.')
    doc2 = Document('doc2', 'Another document for good measure.')
    preprocessor.preprocess_new([doc1, doc2])
    preprocessor.preprocess_doc_pair(doc1, doc2)
    assert len(doc1.vocab.keys()) == 3


def test_preprocessed_voc_contains_short_tokens(preprocessed_docs):
    doc = preprocessed_docs[0]
    assert any(len(token) < 2 for token in doc.vocab)


def test_preprocessed_voc_contains_only_lowercase_tokens(preprocessed_docs):
    doc = preprocessed_docs[0]
    assert any(token.islower() for token in doc.vocab)


def test_preprocessed_sent_start_end_chars(preprocessed_docs):
    doc = preprocessed_docs[1]
    assert [(sent.start_char, sent.end_char) for sent in doc.sents] == [(0, 177), (178, 231), (232, 331)]


def test_preprocessed_sent_start_end_chars_after_join(preprocessor_eng):
    doc1 = Document('doc1', 'Short sentence. Short sentence should be joined with this one.')
    doc2 = Document('doc2', 'Another document for good measure.')
    preprocessor_eng.preprocess_new([doc1, doc2])
    preprocessor_eng.preprocess_doc_pair(doc1, doc2)
    # First sentence: (0, 15)
    # Second sentence: (16, 46)
    # Combined: (0, 62) because of whitespace gap between sents
    assert len(doc1.sents) == 1
    assert (doc1.sents[0].start_char, doc1.sents[0].end_char) == (0, 62)


def test_preprocessed_sent_bows(preprocessed_docs):
    doc = preprocessed_docs[0]
    # Lemma error "rights" ignored
    assert [sent.bow for sent in doc.sents] == [
        Counter({'plagiarism': 1, 'be': 1, 'not': 1, 'the': 1, 'same': 1, 'as': 1, 'copyright': 1, 'infringement': 1}),
        Counter({'while': 1, 'both': 1, 'term': 1, 'may': 1, 'apply': 1, 'to': 1, 'a': 1, 'particular': 1, 'act': 1,
                 'they': 1, 'be': 1, 'different': 1, 'concept': 1}),
        Counter({'copyright': 3, 'be': 3, 'a': 2, 'of': 2, 'use': 2, 'infringement': 1, 'violation': 1, 'the': 1,
                 'rights': 1, 'holder': 1, 'when': 1, 'material': 1, 'whose': 1, 'restrict': 1, 'by': 1, 'without': 1,
                 'consent': 1})]


def test_preprocessed_not_any_of_sent_bows_empty(preprocessor_ger):
    doc1 = Document('doc1', 'Das ist ein schöner Satz.\n\nNoch ein schöner Satz.')
    doc2 = Document('doc2', 'Another document for good measure.')
    preprocessor_ger.preprocess_new([doc1, doc2])
    preprocessor_ger.preprocess_doc_pair(doc1, doc2)
    assert len([sent.bow for sent in doc1.sents]) == 2
    assert any([len(sent.bow) for sent in doc1.sents])


def test_preprocessed_bows_contains_only_lowercase_tokens(preprocessed_docs):
    doc = preprocessed_docs[0]
    for sent in doc.sents:
        bow = sent.bow
        assert any([token.islower() for token in bow])


def test_join_small_sents_at_start(preprocessor_eng):
    doc1 = Document('doc1', 'Short sentence. Short sentence should be joined with this one.')
    doc2 = Document('doc2', 'Another document for good measure.')
    preprocessor_eng.preprocess_new([doc1, doc2])
    preprocessor_eng.preprocess_doc_pair(doc1, doc2)
    assert len(doc1.sents) == 1
    assert [sent.bow for sent in doc1.sents] == \
           [Counter({'short': 2, 'sentence': 2, 'should': 1, 'be': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1})]
    assert doc1.vocab == Counter(
        {'sentence': 1, 'short': 1, 'this': 1, 'should': 1, 'one': 1, 'be': 1, 'with': 1, 'join': 1})


def test_join_small_sents_in_the_middle(preprocessor_eng):
    doc1 = Document('doc1', 'This is a long sentence. Short sentence. Short sentence should be '
                            'joined with this one.')
    doc2 = Document('doc2', 'Another document for good measure.')
    preprocessor_eng.preprocess_new([doc1, doc2])
    preprocessor_eng.preprocess_doc_pair(doc1, doc2)
    assert len(doc1.sents) == 2
    assert [sent.bow for sent in doc1.sents] == \
           [Counter({'this': 1, 'be': 1, 'a': 1, 'long': 1, 'sentence': 1}),
            Counter({'short': 2, 'sentence': 2, 'should': 1, 'be': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1})]
    assert doc1.vocab == Counter(
        {'be': 2, 'sentence': 2, 'this': 2, 'a': 1, 'long': 1, 'short': 1, 'one': 1, 'join': 1, 'with': 1, 'should': 1})


def test_join_small_sents_at_the_end(preprocessor_eng):
    doc1 = Document('doc1', 'This is a long sentence. Short sentence should be '
                            'joined with this one. Short sentence.')
    doc2 = Document('doc2', 'Another document for good measure.')
    preprocessor_eng.preprocess_new([doc1, doc2])
    preprocessor_eng.preprocess_doc_pair(doc1, doc2)
    assert len(doc1.sents) == 2
    assert [sent.bow for sent in doc1.sents] == \
           [Counter({'this': 1, 'be': 1, 'a': 1, 'long': 1, 'sentence': 1}),
            Counter({'short': 2, 'sentence': 2, 'should': 1, 'be': 1, 'join': 1, 'with': 1, 'this': 1, 'one': 1})]
    assert doc1.vocab == Counter(
        {'be': 2, 'sentence': 2, 'this': 2, 'a': 1, 'long': 1, 'short': 1, 'one': 1, 'join': 1, 'with': 1, 'should': 1})


def test_tf_isf_sent_bows(preprocessed_docs):
    doc1, doc2 = preprocessed_docs
    # Lemma error "rights" ignored
    # Example for copyright in third sent:
    # tf-isf = tf x ln(N/sf)
    # tf('copyright') in sent3 = 3
    # N (num of all sents) = 6
    # sf (num of sents containing 'copyright') = 3
    # tf-isf = 3 x ln(6/3) = 2.0794...
    assert [sent.bow_tf_isf for sent in doc1.sents] == \
           [Counter({'not': 1.0986122886681098, 'same': 1.0986122886681098, 'as': 1.0986122886681098,
                     'copyright': 0.6931471805599453, 'infringement': 0.6931471805599453,
                     'plagiarism': 0.4054651081081644, 'be': 0.1823215567939546, 'the': 0.1823215567939546}),
            Counter({'while': 1.791759469228055, 'both': 1.791759469228055, 'term': 1.791759469228055,
                     'apply': 1.791759469228055, 'particular': 1.791759469228055, 'they': 1.791759469228055,
                     'different': 1.791759469228055, 'concept': 1.791759469228055, 'may': 1.0986122886681098,
                     'to': 1.0986122886681098, 'act': 1.0986122886681098, 'a': 0.4054651081081644,
                     'be': 0.1823215567939546}),
            Counter({'use': 3.58351893845611, 'of': 2.1972245773362196, 'copyright': 2.0794415416798357,
                     'violation': 1.791759469228055, 'rights': 1.791759469228055, 'holder': 1.791759469228055,
                     'when': 1.791759469228055, 'material': 1.791759469228055, 'whose': 1.791759469228055,
                     'restrict': 1.791759469228055, 'by': 1.791759469228055, 'without': 1.791759469228055,
                     'consent': 1.791759469228055, 'a': 0.8109302162163288, 'infringement': 0.6931471805599453,
                     'be': 0.5469646703818638, 'the': 0.1823215567939546})]
