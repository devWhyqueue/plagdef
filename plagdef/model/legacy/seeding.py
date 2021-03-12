import math


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
                v1 = self._cosine_measure(legacy_obj.susp_bow[c], legacy_obj.src_bow[r])
                v2 = self._dice_coeff(legacy_obj.susp_bow[c], legacy_obj.src_bow[r])
                if v1 > legacy_obj.th1 and v2 > legacy_obj.th2:
                    ps.append((c, r, v1, v2))
        return ps

    def _cosine_measure(self, d1, d2):
        """
        DESCRIPTION: Compute the cosine measure (cosine of the angle between two vectors) in sparse (dictionary)
        representation
        INPUT: d1 <dictionary> - Sparse vector 1
               d2 <dictionary> - Sparse vector 2
        OUTPUT: Cosine measure
        """
        dot_prod = 0.0
        det = self._eucl_norm(d1) * self._eucl_norm(d2)
        if det == 0:
            return 0
        for word in d1.keys():
            if word in d2:
                dot_prod += d1[word] * d2[word]
        return dot_prod / det

    def _dice_coeff(self, d1, d2):
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

    def _eucl_norm(self, d1):
        """
        DESCRIPTION: Compute the Euclidean norm of a sparse vector
        INPUT: d1 <dictionary> - sparse vector representation
        OUTPUT: Norm of the sparse vector d1
        """
        norm = 0.0
        for val in d1.values():
            norm += float(val * val)
        return math.sqrt(norm)
