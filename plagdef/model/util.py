from numpy import dot
from numpy.linalg import norm


def cos_sim(bow1: dict, bow2: dict):
    """
    Compute the cosine similarity cos-sim = sum_i=1_n{a_i * b_i} / sqrt{sum_i=1_n{(a_i)^2}} * sqrt{sum_i=1_n{(
    b_i)^2}}
    """
    aligned_vecs = [(bow1[lemma], bow2[lemma]) for lemma in bow1 if lemma in bow2]
    a, b = [v[0] for v in aligned_vecs], [v[1] for v in aligned_vecs]
    return dot(a, b) / (norm(list(bow1.values())) * norm(list(bow2.values())))


def dice_sim(bow1: dict, bow2: dict):
    """
    Compute the dice similarity dice-coeff = 2 * n_com / (n_x + n_y), n_t being the number of distinct common
    lemmas in both sents, n_1 the number of lemmas in sent1 and n_2 the number of lemmas in sent2
    """
    n_com = len(set(bow1.keys()).intersection(bow2.keys()))
    return 2 * n_com / float(len(bow1) + len(bow2))
