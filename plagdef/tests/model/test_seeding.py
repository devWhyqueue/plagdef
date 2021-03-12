from collections import Counter

from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.preprocessing import Sentence
from plagdef.model.seeding import SentenceMatch
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import config, sent_matcher


def test_seeding_returns_seeds(sent_matcher, config):
    doc1_sent_bows = doc2_sent_bows = [Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}),
                                       Counter({'the': 2, 'all': 1, 'word': 1, 'be': 1, 'same': 1}),
                                       Counter({'even': 1, 'these': 1, 'last': 1, 'one': 1, 'be': 1})]
    obj = SGSPLAG('This is a document. All the words are the same. Even these last ones are.',
                  'This is a document. All the words are the same. Even these last ones are.', config)
    obj.susp_bow, obj.src_bow = doc1_sent_bows, doc2_sent_bows
    seeds = sent_matcher.seeding(obj)
    assert len(seeds) == len(doc1_sent_bows)
    assert [s[:2] for s in seeds] == [(0, 0), (1, 1), (2, 2)]


def test_match_returns_nothing_if_not_similar(sent_matcher):
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}))
    sen2 = Sentence(None, -1, -1, Counter({'these': 1, 'however': 1, 'be': 1, 'different': 1, 'word': 1}))
    match = sent_matcher.match(sen1, sen2)
    assert not match


def test_match_returns_match_if_similar(sent_matcher):
    sen1 = sen2 = Sentence(None, -1, -1, Counter({'the': 2, 'all': 1, 'word': 1, 'be': 1, 'same': 1}))
    match = sent_matcher.match(sen1, sen2)
    assert match == SentenceMatch(sen1, sen2, 0.9999999999999998, 1)


def test_cosine_measure(sent_matcher):
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}))
    sen2 = Sentence(None, -1, -1, Counter({'this': 1, 'also': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1}))
    sim = sent_matcher._cos_sim(sen1, sen2)
    # cos-sim = sum_i=1_n{a_i * b_i} / sqrt{sum_i=1_n{(a_i)^2}} * sqrt{sum_i=1_n{(b_i)^2}}
    # sum_i=1_n{a_i * b_i}:
    #   'this', 'be', 'a' and 'document' are in both bows -> their term freqs are considered (otherwise 0 anyway)
    #   = (1*1) + (1*1) + (1*1) + (1*1) = 4
    # sqrt{sum_i=1_n{(a_i)^2}} (eucl_norm of a):
    #  = srqt{1 + 1 + 1 + 1} = 2
    # sqrt{sum_i=1_n{(b_i)^2}} (eucl_norm of b):
    #  = srqt{1 + 1 + 1 + 1 + 4 + 1} = 3
    # eucl_norm(a) * eucl_norm(b) = 6
    # cos-sim = 4 / 6 = 0.6666...
    assert sim == 0.6666666666666666


def test_dice_coeff(sent_matcher):
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1}))
    sen2 = Sentence(None, -1, -1, Counter({'this': 1, 'also': 1, 'be': 1, 'a': 1, 'great': 2, 'document': 1}))
    sim = sent_matcher._dice_sim(sen1, sen2)
    # dice-coeff = 2 * n_t / (n_x + n_y), n_t being the number of equal lemmas in both sents (independent from their
    # term freq), n_x the number of lemmas in x and n_y the number of lemmas in y
    # n_t = |bow1| = 5, n_x = 5, n_y = 6
    # dice-coeff = 2 * 5 / (5 + 6) = 10 / 11 = 0.9090...
    assert sim == 0.9090909090909091
