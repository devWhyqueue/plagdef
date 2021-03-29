from collections import Counter

from plagdef.model.preprocessing import Sentence, Document
from plagdef.model.util import cos_sim, dice_sim, adjacent, cluster_tf_isf_bow
from plagdef.tests.fakes import FakeSentence


def test_cosine_measure(seeder):
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1: 'This is a nice document. It really is.'
    # doc2: 'This also is a great document. Even better one might say.'
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}),
                    {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69})
    sen2 = Sentence(None, -1, -1, Counter({'this': 1, 'also': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1}),
                    {'this': 0.69, 'also': 1.38, 'be': 0.28, 'a': 0.69, 'great': 1.38, 'document': 0.69})
    sim = cos_sim(sen1.bow_tf_isf, sen2.bow_tf_isf)
    # cos-sim = sum_i=1_n{a_i * b_i} / sqrt{sum_i=1_n{(a_i)^2}} * sqrt{sum_i=1_n{(b_i)^2}}
    # sum_i=1_n{a_i * b_i}:
    #   'this', 'be', 'a' and 'document' are in both bows -> their term freqs are considered (otherwise 0 anyway)
    #   = (0.69*0.69) + (0.28*0.28) + (0.69*0.69) + (0.69*0.69) = 1.5067
    # sqrt{sum_i=1_n{(a_i)^2}} (eucl_norm of a):
    #  = srqt{0.69^2 + 0.28^2 + 0.69^2 + 1.38^2 + 0.69^2} = 1.8469...
    # sqrt{sum_i=1_n{(b_i)^2}} (eucl_norm of b):
    #  = srqt{0.69^2 + 1.38^2 + 0.28^2 + 0.69^2 + 1.38^2 + 0.69^2} = 2.3055....
    # eucl_norm(a) * eucl_norm(b) = 4.2581...
    # cos-sim = 1.5067 / 4.2581... = 0.3538...
    assert sim == 0.35384046845354156


def test_dice_coeff(seeder):
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1: 'This is a nice document. It really is.'
    # doc2: 'This also is a great document. Even better one might say.'
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}),
                    {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69})
    sen2 = Sentence(None, -1, -1, Counter({'this': 1, 'also': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1}),
                    {'this': 0.69, 'also': 1.38, 'be': 0.28, 'a': 0.69, 'great': 1.38, 'document': 0.69})
    sim = dice_sim(sen1.bow_tf_isf, sen2.bow_tf_isf)
    # dice-coeff = 2 * n_t / (n_x + n_y), n_t being the number of equal lemmas in both sents (independent from their
    # term freq), n_x the number of lemmas in x and n_y the number of lemmas in y
    # n_t = 4, n_x = 5, n_y = 6
    # dice-coeff = 2 * 4 / (5 + 6) = 8 / 11 = 0.7272...
    assert sim == 0.7272727272727273


def test_adjacent_sents():
    sent1 = _create_sent('doc1', 0)
    sent2 = _create_sent('doc2', 5)
    adj = adjacent(sent1, sent2, 4)
    assert adj


def test_adjacent_sents_with_gap_over_th():
    sent1 = _create_sent('doc1', 0)
    sent2 = _create_sent('doc2', 6)
    # Five sentences in-between
    adj = adjacent(sent1, sent2, 4)
    assert not adj


def test_cluster_tf_isf_bow(preprocessor_eng):
    doc1 = Document('doc1', 'This is an awesome document. All of these bows are combined. Even this last one.')
    doc2 = Document('doc2', 'This is another document. Just for good measure. As always.')
    preprocessor_eng.preprocess_new([doc1, doc2])
    preprocessor_eng.preprocess_doc_pair(doc1, doc2)
    # doc1:
    # First bow: {'this': 0.22, 'be': 0.51, 'a': 1.60, 'awesome': 1.60, 'document': 0.91}
    # Second bow: {'all': 1.60, 'of': 1.60, 'this': 0.22, 'bow': 1.60, 'be': 0.51, 'combine': 1.60}
    # Third bow: {'even': 1.60, 'this': 0.22, 'last': 1.60, 'one': 1.60}
    combined_bow = cluster_tf_isf_bow(doc1, 0, 2)
    assert combined_bow == {'this': 0.6694306539426294, 'be': 1.0216512475319814,
                            'a': 1.6094379124341003, 'awesome': 1.6094379124341003, 'document': 0.9162907318741551,
                            'all': 1.6094379124341003, 'of': 1.6094379124341003, 'bow': 1.6094379124341003,
                            'combine': 1.6094379124341003, 'even': 1.6094379124341003, 'last': 1.6094379124341003,
                            'one': 1.6094379124341003}


def _create_sent(doc_name: str, sent_idx: int):
    doc1 = Document(doc_name, '')
    return FakeSentence(doc1, sent_idx, -1, -1, Counter(), {})
