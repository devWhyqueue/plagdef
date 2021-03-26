from plagdef.model.legacy.util import cosine_measure, dice_coeff


class LegacySentenceMatcher:
    def seeding(self, legacy_obj):
        """
        DESCRIPTION: Creates the seeds from pair of sentece similarity using dice and cosine similarity
        INPUT: self <SGSPLAG object>
        OUTPUT: ps <list of tuple (int, int, float, float)> - Seeds
        """
        ps = []
        for c in range(len(legacy_obj.susp_bow)):
            for r in range(len(legacy_obj.src_bow)):
                v1 = cosine_measure(legacy_obj.susp_bow[c], legacy_obj.src_bow[r])
                v2 = dice_coeff(legacy_obj.susp_bow[c], legacy_obj.src_bow[r])
                if v1 > legacy_obj.th1 and v2 > legacy_obj.th2:
                    ps.append((c, r, v1, v2))
        return ps
