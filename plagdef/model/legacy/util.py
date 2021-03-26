import copy
import math


def sum_vect(dic1, dic2):
    """
    DESCRIPTION: Adding two vectors in form of dictionaries (sparse vectors or inverted list)
    INPUTS: dic1 <dictionary> - Vector 1
            dic2 <dictionary> - Vector 2
    OUTPUT: res <dictionary> - Sum of the two vectors
    """
    res = copy.deepcopy(dic1)
    for i in dic2.keys():
        if i in res:
            res[i] += dic2[i]
        else:
            res[i] = dic2[i]
    return res


def dice_coeff(d1, d2):
    """
    DESCRIPTION: Compute the dice coefficient in sparse (dictionary) representation
    INPUT: d1 <dictionary> - Sparse vector 1
           d2 <dictionary> - Sparse vector 2
    OUTPUT: Dice coefficient
    """
    if len(d1) + len(d2) == 0:
        return 0
    intj = 0
    for i in d1.keys():
        if i in d2:
            intj += 1
    return 2 * intj / float(len(d1) + len(d2))


def cosine_measure(d1, d2):
    """
    DESCRIPTION: Compute the cosine measure (cosine of the angle between two vectors) in sparse (dictionary)
    representation
    INPUT: d1 <dictionary> - Sparse vector 1
           d2 <dictionary> - Sparse vector 2
    OUTPUT: Cosine measure
    """
    dot_prod = 0.0
    det = _eucl_norm(d1) * _eucl_norm(d2)
    if det == 0:
        return 0
    for word in d1.keys():
        if word in d2:
            dot_prod += d1[word] * d2[word]
    return dot_prod / det


def _eucl_norm(d1):
    """
    DESCRIPTION: Compute the Euclidean norm of a sparse vector
    INPUT: d1 <dictionary> - sparse vector representation
    OUTPUT: Norm of the sparse vector d1
    """
    norm = 0.0
    for val in d1.values():
        norm += float(val * val)
    return math.sqrt(norm)
