from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.legacy.seeding import LegacySentenceMatcher


def test_seeding_returns_seeds(config):
    doc1_sent_bows = doc2_sent_bows = [{'this': 1.0986, 'be': 0.0, 'a': 1.0986, 'document': 1.0986},
                                       {'all': 1.0986, 'the': 2.1972, 'word': 1.0986, 'be': 0.0, 'same': 1.0986},
                                       {'even': 1.0986, 'these': 1.0986, 'last': 1.0986, 'one': 1.0986, 'be': 0.0}]
    obj = SGSPLAG('This is a document. All the words are the same. Even these last ones are.',
                  'This is a document. All the words are the same. Even these last ones are.', config)
    obj.susp_bow, obj.src_bow = doc1_sent_bows, doc2_sent_bows
    sent_matcher = LegacySentenceMatcher()
    seeds = sent_matcher.seeding(obj)
    assert len(seeds) == len(doc1_sent_bows)
    assert [s[:2] for s in seeds] == [(0, 0), (1, 1), (2, 2)]


def test_cosine_measure():
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1: 'This is a nice document. It really is.'
    # doc2: 'This also is a great document. Even better one might say.'
    bow1 = {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69}
    bow2 = {'this': 0.69, 'also': 1.38, 'be': 0.28, 'a': 0.69, 'great': 1.38, 'document': 0.69}
    sent_matcher = LegacySentenceMatcher()
    sim = sent_matcher._cosine_measure(bow1, bow2)
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


def test_eucl_norm():
    bow = {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69}
    sent_matcher = LegacySentenceMatcher()
    norm = sent_matcher._eucl_norm(bow)
    # eucl_norm = sqrt{sum_i=1_n{(a_i)^2}} = srqt{0.69^2 + 0.28^2 + 0.69^2 + 1.38^2 + 0.69^2} = 1.8469...
    assert norm == 1.8469163489449107


def test_dice_coeff():
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1: 'This is a nice document. It really is.'
    # doc2: 'This also is a great document. Even better one might say.'
    bow1 = {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69}
    bow2 = {'this': 0.69, 'also': 1.38, 'be': 0.28, 'a': 0.69, 'great': 1.38, 'document': 0.69}
    sent_matcher = LegacySentenceMatcher()
    sim = sent_matcher._dice_coeff(bow1, bow2)
    # dice-coeff = 2 * n_t / (n_x + n_y), n_t being the number of equal lemmas in both sents (independent from their
    # term freq), n_x the number of lemmas in x and n_y the number of lemmas in y
    # n_t = 4, n_x = 5, n_y = 6
    # dice-coeff = 2 * 4 / (5 + 6) = 8 / 11 = 0.7272...
    assert sim == 0.7272727272727273
