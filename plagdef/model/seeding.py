from plagdef.model import util
from plagdef.model.models import Seed
from plagdef.model.preprocessing import Sentence, Document


class Seeder:
    def __init__(self, min_cos_sim: float, min_dice_sim: float):
        self._min_cos_sim = min_cos_sim
        self._min_dice_sim = min_dice_sim

    def seed(self, doc1: Document, doc2: Document):
        seeds = []
        for doc1_sent in doc1.sents:
            for doc2_sent in doc2.sents:
                seed = self._match(doc1_sent, doc2_sent)
                if seed:
                    seeds.append(seed)
        return seeds

    # TODO: Only for backwards compatibility
    def seeding(self, legacy_obj):
        sent_matches = []
        for doc1_sent_num in range(len(legacy_obj.susp_bow)):
            for doc2_sent_num in range(len(legacy_obj.src_bow)):
                match = self._match(Sentence(None, -1, -1, None, legacy_obj.susp_bow[doc1_sent_num]),
                                    Sentence(None, -1, -1, None, legacy_obj.src_bow[doc2_sent_num]))
                if match:
                    sent_matches.append((doc1_sent_num, doc2_sent_num, match.cos_sim, match.dice_sim))
        return sent_matches

    def _match(self, sent1: Sentence, sent2: Sentence):
        cos_sim = util.cos_sim(sent1.tf_isf_bow, sent2.tf_isf_bow)
        dice_sim = util.dice_sim(sent1.tf_isf_bow, sent2.tf_isf_bow)
        if cos_sim > self._min_cos_sim and dice_sim > self._min_dice_sim:
            return Seed(sent1, sent2, cos_sim, dice_sim)
