from plagdef.model.legacy.util import cosine_measure, sum_vect


class LegacySeedExtender:

    def extend(self, legacy_obj, ps):
        """
        DESCRIPTION: Adding two vectors
        INPUT: self <SGSPLAG object>
               ps <list of tuple (int, int, float, float)> - Seeds
        OUTPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases after
        validation
                psr <list of list of tuples (int, int)> - Contains the clusters after validation
                sim_frag <list of floats> - Stores the cosine similarity between source and suspicios fragments in
                the plagiarism cases after validation
        """
        psr = self._clustering(ps, legacy_obj.src_offsets, legacy_obj.susp_offsets, legacy_obj.src_gap,
                               legacy_obj.susp_gap, legacy_obj.src_size,
                               legacy_obj.susp_size, 0, 0)
        plags = []
        for psr_i in psr:  # For every cluster
            plags.append([(min([x[0] for x in psr_i]), max([x[0] for x in psr_i])),  # Case: First to last seed in doc1
                          (min([x[1] for x in psr_i]), max([x[1] for x in psr_i]))])  # Case: First to last seed in doc2
        temp_res = self._validation(plags, psr, legacy_obj.src_offsets, legacy_obj.susp_offsets, legacy_obj.src_bow,
                                    legacy_obj.susp_bow,
                                    legacy_obj.src_gap, legacy_obj.src_gap_least, legacy_obj.susp_gap,
                                    legacy_obj.susp_gap_least, legacy_obj.src_size,
                                    legacy_obj.susp_size, legacy_obj.th3)
        if len(temp_res) == 0:
            plags, psr, sim_frag = [], [], []
        else:
            plags, psr, sim_frag = temp_res[0], temp_res[1], temp_res[2]
        return plags, psr, sim_frag

    # Offsets are not needed
    def _clustering(self, ps, src_offsets, susp_offsets, src_gap, susp_gap, src_size, susp_size, side, times):
        """
        DESCRIPTION: Generates the clusters of seeds
        INPUT: ps <list of tuples (int, int)> - Seeds
               src_offsets <list of tuples (int, int)> - Contain the char offset and length of each source document
               sentence
               susp_offsets <list of tuples (int, int)> - Contain the char offset and length of each suspicious document
               sentence
               src_gap <int> - Max gap between sentences to be consider adjacent in the source document
               susp_gap <int> - Max gap between sentences to be consider adjacent in the suspicious document
               src_size <int> - Minimum amount of sentences in a plagiarism case in the side of source document
               susp_size <int> - Minimum amount of sentences in a plagiarism case in the side of suspicious document
               side <0 or 1> 0: Suspicious document side, 1: Source document side
               times <int> - Counts how many times clustering() have been called
        OUTPUT: res <list of list of tuples (int, int)> - Contains the clusters
        """
        # Find clusters (lists of seeds)
        ps_sets = self._frag_founder(ps, src_gap, susp_gap, src_size, susp_size, side)
        res = []
        if len(ps_sets) <= 1 and times > 0:
            return ps_sets
        else:  # First time or they is more than one cluster in doc
            times += 1
            for i in ps_sets:  # For every cluster in doc (side)
                # Do the same for other doc
                partial_res = self._clustering(i, src_offsets, susp_offsets, src_gap, susp_gap, src_size, susp_size,
                                               (side + 1) % 2, times)
                res.extend(partial_res)
        return res

    def _frag_founder(self, ps, src_gap, susp_gap, src_size, susp_size, side):
        """
        DESCRIPTION: Form clusters by grouping "adjacent" sentences in a given side (source o suspicious)
        INPUT: ps <list of tuples (int, int)> - Seeds
               src_offsets <list of tuples (int, int)> - Contain the char offset and length of each source document
               sentence
               susp_offsets <list of tuples (int, int)> - Contain the char offset and length of each suspicious document
               sentence
               src_gap <int> - Max gap between sentences to be consider adjacent in the source document
               susp_gap <int> - Max gap between sentences to be consider adjacent in the suspicious document
               src_size <int> - Minimum amount of sentences in a plagiarism case in the side of source document
               susp_size <int> - Minimum amount of sentences in a plagiarism case in the side of suspicious document
               side <0 or 1> 0: Suspicious document side, 1: Source document side
        OUTPUT: res <list of list of tuples (int, int)> - Contains the clusters
        """
        if side == 0:  # Configure params from config
            max_gap = susp_gap
            min_size = susp_size
        else:
            max_gap = src_gap
            min_size = src_size
        res = []  # all clusters
        ps.sort(key=lambda tup: tup[side])  # Sort seeds by occurrence in doc1/doc2 (side=0,side=1)
        sub_set = []  # cluster_i
        for pair in ps:  # For every seed
            if len(sub_set) == 0:  # Append first seed no matter what
                sub_set.append(pair)
            else:  # Every other seed
                # Check whether seed is adjacent to last one in this doc (1 or 2)
                if self._adjacent_sents(pair[side], sub_set[-1][side], max_gap):
                    sub_set.append(pair)
                else:  # Not adjacent anymore
                    if len(sub_set) >= min_size:  # If at least one seed was adjacent or is first seed
                        res.append(sub_set)
                    sub_set = [pair]  # sub_set contains last seed
        # If last seed was adjacent to predecessor(s) add it to clusters
        if len(sub_set) >= min_size:
            res.append(sub_set)
        return res

    def _adjacent_sents(self, a, b, th):
        """
        DESCRIPTION: Define if two sentences are adjacent measured in sentences
        INPUT: a <int> - Sentence a index,
               b <int> - Sentence b index
               th <int> - maximum gap between indexes
        OUTPUT: True if the two sentences are adjacents, False otherwise
        """
        if abs(a - b) - 1 <= th:
            return True
        else:
            return False

    def _validation(self, plags, psr, src_offsets, susp_offsets, src_bow, susp_bow, src_gap, src_gap_least, susp_gap,
                    susp_gap_least, src_size, susp_size, th3):
        """
        DESCRIPTION: Compute the similarity of the resulting plagiarism cases from extension. In case of being below
        certain threshold extension is applied again with max_gap - 1
        INPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Have the plagiarism cases represented by
        min
        and max sentence index in suspicious and source document respectively
               psr <list of list of tuples (int, int)> - Contains the clusters
               src_offsets <list of tuples (int, int)> - Contain the char offset and length of each source document
               sentence
               susp_offsets <list of tuples (int, int)> - Contain the char offset and length of each suspicious document
               sentence
               src_bow <list of dictionaries> - Bag of words representing each sentence vector of source document
               susp_bow <list of dictionaries> - Bag of words representing each sentence vector of suspicious document
               src_gap <int> - Max gap between sentences to be consider adjacent in the source document
               src_gap_least <int> - Smallest value the max gap between sentences considerd adjacent can gets in the
               source document
               susp_gap <int> - Max gap between sentences to be consider adjacent in the suspicious document
               susp_gap_least <int> - Smallest value the max gap between sentences considerd adjacent can gets in the
               suspicious document
               src_size <int> - Minimum amount of sentences in a plagiarism case in the side of source document
               susp_size <int> - Minimum amount of sentences in a plagiarism case in the side of suspicious document
               th3 <float> - Threshold for the minimum cosine similarity between source and suspicios fragments in a
               plagiarism case
        OUTPUT: res_plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases that
        passed the validation process
                res_psr <list of list of tuples (int, int)> - Contains the clusters that passed the validation process
                res_sim_frag <list of floats> - Stores the cosine similarity between source and suspicios fragments in
                the plagiarism cases
        """
        res_plags = []
        res_psr = []
        res_sim_frag = []
        i = 0
        range_i = len(plags)
        while i < range_i:  # For each case [(sent_start_idx, sent_end_idx), (sent_start_idx, sent_end_idx)]
            susp_d = {}
            for j in range(plags[i][0][0], plags[i][0][1] + 1):  # For each sentence in doc1
                susp_d = sum_vect(susp_d, susp_bow[j])  # Sum up all sentence vectors
            src_d = {}
            for j in range(plags[i][1][0], plags[i][1][1] + 1):  # For each sentence in doc2
                src_d = sum_vect(src_d, src_bow[j])  # Sum up all sentence vectors
            sim_frag = cosine_measure(src_d, susp_d)  # Calculate similarity between fragments
            if sim_frag <= th3:  # If not similar enough
                # Try to extend again but with smaller adjacent_sent_gap
                if src_gap > src_gap_least and susp_gap > susp_gap_least:  # Do until substraction +1
                    new_psr = self._clustering(psr[i], src_offsets, susp_offsets, src_gap - 1, susp_gap - 1, src_size,
                                               susp_size,
                                               0, 0)
                    new_plags = []
                    for ps_set in new_psr:
                        new_plags.append([(min([x[0] for x in ps_set]), max([x[0] for x in ps_set])),
                                          (min([x[1] for x in ps_set]), max([x[1] for x in ps_set]))])
                    if len(new_plags) == 0:
                        return []
                    temp_res = self._validation(new_plags, new_psr, src_offsets, susp_offsets, src_bow, susp_bow,
                                                src_gap - 1,
                                                src_gap_least, susp_gap - 1, susp_gap_least, src_size, susp_size, th3)
                    if len(temp_res) == 0:
                        plags_rec, psr_rec, res_sim_frag_rec = [], [], []
                    else:
                        plags_rec, psr_rec, res_sim_frag_rec = temp_res[0], temp_res[1], temp_res[2]
                    if len(plags_rec) != 0:  # Found some new cases after reduction of adjacent_sent_gap
                        res_plags.extend(plags_rec)  # Add them to result
                        res_psr.extend(psr_rec)
                        res_sim_frag.extend(res_sim_frag_rec)
                i += 1
            else:  # If sentences in case are similar enough
                # Passed with src_gap
                res_plags.append(plags[i])  # Add plag case
                res_psr.append(psr[i])  # Add cluster
                res_sim_frag.append(sim_frag)  # Add similarity
                i += 1
        return res_plags, res_psr, res_sim_frag
