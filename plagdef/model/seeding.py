from dataclasses import dataclass

from numpy import dot
from numpy.linalg import norm

from plagdef.model.preprocessing import Sentence


@dataclass(frozen=True)
class SentenceMatch:
    sent1: Sentence
    sent2: Sentence
    cos_sim: float
    dice_sim: float


class SentenceMatcher:
    def __init__(self, min_cos_sim: float, min_dice_sim: float):
        self._min_cos_sim = min_cos_sim
        self._min_dice_sim = min_dice_sim

    def match(self, sent1: Sentence, sent2: Sentence):
        cos_sim = self._cos_sim(sent1, sent2)
        dice_sim = self._dice_sim(sent1, sent2)
        if cos_sim > self._min_cos_sim and dice_sim > self._min_dice_sim:
            return SentenceMatch(sent1, sent2, cos_sim, dice_sim)

    def _cos_sim(self, sent1: Sentence, sent2: Sentence):
        """
        Compute the cosine similarity cos-sim = sum_i=1_n{a_i * b_i} / sqrt{sum_i=1_n{(a_i)^2}} * sqrt{sum_i=1_n{(
        b_i)^2}}
        """
        aligned_vecs = [(sent1.bow[lemma], sent2.bow[lemma]) for lemma in sent1.bow.keys() if lemma in sent2.bow.keys()]
        a, b = [v[0] for v in aligned_vecs], [v[1] for v in aligned_vecs]
        return dot(a, b) / (norm(list(sent1.bow.values())) * norm(list(sent2.bow.values())))

    def _dice_sim(self, sent1: Sentence, sent2: Sentence):
        """
        Compute the dice similarity dice-coeff = 2 * n_com / (n_x + n_y), n_t being the number of distinct common
        lemmas in both sents, n_1 the number of lemmas in sent1 and n_2 the number of lemmas in sent2
        """
        n_com = len(set(sent1.bow.keys()).intersection(sent2.bow.keys()))
        return 2 * n_com / float(len(sent1.bow) + len(sent2.bow))

    # TODO: Only for backwards compatibility
    def seeding(self, legacy_obj):
        sent_matches = []
        for doc1_sent_num in range(len(legacy_obj.susp_bow)):
            for doc2_sent_num in range(len(legacy_obj.src_bow)):
                match = self.match(Sentence(None, -1, -1, legacy_obj.susp_bow[doc1_sent_num]),
                                   Sentence(None, -1, -1, legacy_obj.src_bow[doc2_sent_num]))
                if match:
                    sent_matches.append((doc1_sent_num, doc2_sent_num, match.cos_sim, match.dice_sim))
        return sent_matches
