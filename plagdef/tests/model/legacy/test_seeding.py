from collections import Counter

from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.legacy.seeding import LegacySentenceMatcher
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import config


def test_seeding_returns_seeds(config):
    doc1_sent_bows = doc2_sent_bows = [Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}),
                                       Counter({'the': 2, 'all': 1, 'word': 1, 'be': 1, 'same': 1}),
                                       Counter({'even': 1, 'these': 1, 'last': 1, 'one': 1, 'be': 1})]
    obj = SGSPLAG('This is a document. All the words are the same. Even these last ones are.',
                  'This is a document. All the words are the same. Even these last ones are.', config)
    obj.susp_bow, obj.src_bow = doc1_sent_bows, doc2_sent_bows
    sent_matcher = LegacySentenceMatcher()
    seeds = sent_matcher.seeding(obj)
    assert len(seeds) == len(doc1_sent_bows)
    assert [s[:2] for s in seeds] == [(0, 0), (1, 1), (2, 2)]


def test_cosine_measure():
    bow1 = Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1})
    bow2 = Counter({'this': 1, 'also': 1, 'be': 1, 'a': 1, 'document': 1})
    sent_matcher = LegacySentenceMatcher()
    sim = sent_matcher._cosine_measure(bow1, bow2)
    # cos-sim = sum_i=1_n{a_i * b_i} / sqrt{sum_i=1_n{(a_i)^2}} * sqrt{sum_i=1_n{(b_i)^2}}
    # sum_i=1_n{a_i * b_i}:
    #   'this', 'be', 'a' and 'document' are in both bows -> their term freqs are considered (otherwise 0 anyway)
    #   = (1*1) + (1*1) + (1*1) + (1*1) = 4
    # sqrt{sum_i=1_n{(a_i)^2}} (eucl_norm of a):
    #  = srqt{1 + 1 + 1 + 1} = 2
    # sqrt{sum_i=1_n{(b_i)^2}} (eucl_norm of b):
    #  = srqt{1 + 1 + 1 + 1 + 1} = 2.2361...
    # eucl_norm(a) * eucl_norm(b) = 4.4721...
    # cos-sim = 4 / 4.4721 = 0.8944...
    assert sim == 0.8944271909999159


def test_eucl_norm():
    bow = Counter({'this': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1})
    sent_matcher = LegacySentenceMatcher()
    norm = sent_matcher._eucl_norm(bow)
    # eucl_norm = sqrt{sum_i=1_n{(a_i)^2}} = = srqt{1 + 1 + 1 + 4 + 1} = 2.8284....
    assert norm == 2.8284271247461903


def test_dice_coeff():
    bow1 = Counter({'this': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1})
    bow2 = Counter({'this': 1, 'also': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1})
    sent_matcher = LegacySentenceMatcher()
    sim = sent_matcher._dice_coeff(bow1, bow2)
    # dice-coeff = 2 * n_t / (n_x + n_y), n_t being the number of equal lemmas in both sents (independent from their
    # term freq), n_x the number of lemmas in x and n_y the number of lemmas in y
    # n_t = |bow1| = 5, n_x = 5, n_y = 6
    # dice-coeff = 2 * 5 / (5 + 6) = 10 / 11 = 0.9090...
    assert sim == 0.9090909090909091
