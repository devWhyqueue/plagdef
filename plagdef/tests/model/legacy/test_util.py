from plagdef.model.legacy.util import dice_coeff, _eucl_norm, cosine_measure, sum_vect


def test_cosine_measure():
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1: 'This is a nice document. It really is.'
    # doc2: 'This also is a great document. Even better one might say.'
    bow1 = {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69}
    bow2 = {'this': 0.69, 'also': 1.38, 'be': 0.28, 'a': 0.69, 'great': 1.38, 'document': 0.69}
    sim = cosine_measure(bow1, bow2)
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
    norm = _eucl_norm(bow)
    # eucl_norm = sqrt{sum_i=1_n{(a_i)^2}} = srqt{0.69^2 + 0.28^2 + 0.69^2 + 1.38^2 + 0.69^2} = 1.8469...
    assert norm == 1.8469163489449107


def test_dice_coeff():
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1: 'This is a nice document. It really is.'
    # doc2: 'This also is a great document. Even better one might say.'
    bow1 = {'this': 0.69, 'be': 0.28, 'a': 0.69, 'nice': 1.38, 'document': 0.69}
    bow2 = {'this': 0.69, 'also': 1.38, 'be': 0.28, 'a': 0.69, 'great': 1.38, 'document': 0.69}
    sim = dice_coeff(bow1, bow2)
    # dice-coeff = 2 * n_t / (n_x + n_y), n_t being the number of equal lemmas in both sents (independent from their
    # term freq), n_x the number of lemmas in x and n_y the number of lemmas in y
    # n_t = 4, n_x = 5, n_y = 6
    # dice-coeff = 2 * 4 / (5 + 6) = 8 / 11 = 0.7272...
    assert sim == 0.7272727272727273


def test_sum_vect(config):
    # This also is a document.
    voc1 = {'this': 1, 'also': 1, 'document': 1}
    # This is a cool document.
    voc2 = {'this': 1, 'cool': 1, 'document': 1}
    combined_voc = sum_vect(voc1, voc2)
    assert combined_voc == {'this': 2, 'also': 1, 'document': 2, 'cool': 1}
