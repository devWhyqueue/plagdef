from collections import Counter

from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.preprocessing import Sentence
from plagdef.model.seeding import SentenceMatch


def test_seeding_returns_seeds(sent_matcher, config):
    doc1_sent_bows = doc2_sent_bows = [{'this': 1.0986, 'be': 0.0, 'a': 1.0986, 'document': 1.0986},
                                       {'all': 1.0986, 'the': 2.1972, 'word': 1.0986, 'be': 0.0, 'same': 1.0986},
                                       {'even': 1.0986, 'these': 1.0986, 'last': 1.0986, 'one': 1.0986, 'be': 0.0}]
    obj = SGSPLAG('This is a document. All the words are the same. Even these last ones are.',
                  'This is a document. All the words are the same. Even these last ones are.', config)
    obj.susp_bow, obj.src_bow = doc1_sent_bows, doc2_sent_bows
    seeds = sent_matcher.seeding(obj)
    assert len(seeds) == len(doc1_sent_bows)
    assert [s[:2] for s in seeds] == [(0, 0), (1, 1), (2, 2)]


def test_match_returns_nothing_if_not_similar(sent_matcher):
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}),
                    {'this': 0.69, 'be': 0.0, 'a': 0.69, 'document': 0.69})
    sen2 = Sentence(None, -1, -1, Counter({'these': 1, 'however': 1, 'be': 1, 'different': 1, 'word': 1}),
                    {'these': 0.69, 'be': 0.0, 'different': 0.69,
                     'word': 0.69, 'however': 0.69})
    match = sent_matcher.match(sen1, sen2)
    assert not match


def test_match_returns_match_if_similar(sent_matcher):
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1/doc2: 'The words are all the same. Even these are.'
    doc1_sent1 = doc2_sent1 = Sentence(None, -1, -1, Counter({'the': 2, 'word': 1, 'be': 1, 'all': 1, 'same': 1}),
                                       {'the': 1.38, 'word': 0.69, 'be': 0.0, 'all': 0.69, 'same': 0.69})
    match = sent_matcher.match(doc1_sent1, doc2_sent1)
    assert match == SentenceMatch(doc1_sent1, doc2_sent1, 1, 1)


def test_cosine_measure(sent_matcher):
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1: 'This is a nice document. It really is.'
    # doc2: 'This also is a great document. Even better one might say.'
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}),
                    {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69})
    sen2 = Sentence(None, -1, -1, Counter({'this': 1, 'also': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1}),
                    {'this': 0.69, 'also': 1.38, 'be': 0.28, 'a': 0.69, 'great': 1.38, 'document': 0.69})
    sim = sent_matcher._cos_sim(sen1, sen2)
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


def test_dice_coeff(sent_matcher):
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1: 'This is a nice document. It really is.'
    # doc2: 'This also is a great document. Even better one might say.'
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}),
                    {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69})
    sen2 = Sentence(None, -1, -1, Counter({'this': 1, 'also': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1}),
                    {'this': 0.69, 'also': 1.38, 'be': 0.28, 'a': 0.69, 'great': 1.38, 'document': 0.69})
    sim = sent_matcher._dice_sim(sen1, sen2)
    # dice-coeff = 2 * n_t / (n_x + n_y), n_t being the number of equal lemmas in both sents (independent from their
    # term freq), n_x the number of lemmas in x and n_y the number of lemmas in y
    # n_t = 4, n_x = 5, n_y = 6
    # dice-coeff = 2 * 4 / (5 + 6) = 8 / 11 = 0.7272...
    assert sim == 0.7272727272727273
