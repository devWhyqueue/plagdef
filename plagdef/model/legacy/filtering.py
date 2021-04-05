from plagdef.model.legacy.util import cosine_measure


class LegacyClusterFilter:

    def filtering(self, leg_obj, plags, psr):
        """
        DESCRIPTION: Filter the plagiarism cases by removing overlapping and short cases
        INPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases after
        validation
               psr <list of list of tuples (int, int)> - Contains the clusters after validation
        OUTPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases. Also
        modify psr.
        """
        plags, psr = self.remove_overlap3(plags, psr, leg_obj.src_bow, leg_obj.susp_bow)
        plags, psr = self.remove_small_plags(plags, psr, leg_obj.src_offsets, leg_obj.susp_offsets,
                                             leg_obj.min_cluster_char_len)

        return plags

    def remove_overlap3(self, plags, psr, src_bow, susp_bow):
        """
        DESCRIPTION: From a set of overlapping plagiarism cases, looking only on the suspicious side, selects the best
        case. See article (1) at the beggining of this file, for the formal description.
        INPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Have the plagiarism cases represented by
        min
        and max sentence index in suspicious and source document respectively
               psr <list of list of tuples (int, int)> - Contains the clusters
               src_bow <list of dictionaries> - Bag of words representing each sentence vector of source document
               susp_bow <list of dictionaries> - Bag of words representing each sentence vector of suspicious document
        OUTPUT: res_plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases without
        overlapping
                res_psr <list of list of tuples (int, int)> - Contains the clusters without overlapping
        """
        if len(plags) != 0:
            # Combine plags with clusters sorted by min sent_idx in sups doc to separate lists
            plags, psr = map(list, zip(*sorted(zip(plags, psr), key=lambda tup: tup[0][0][0])))
        res_plags = []
        res_psr = []
        flag = 0  # Did some case overlap until now?
        i = 0
        while i < len(plags):  # For each plag case
            cont_ol = 0  # number of overlapping sents
            if flag == 0:
                for k in range(i + 1, len(plags)):  # For following cases
                    if plags[k][0][0] - plags[i][0][1] <= 0:  # If min_sent_idx of successor <= max_sent_idx of case
                        cont_ol += 1
            else:
                for k in range(i + 1, len(plags)):  # For following cases
                    # If min_sent_idx of successor <= max_sent_idx of last added case
                    if plags[k][0][0] - res_plags[-1][0][1] <= 0:
                        cont_ol += 1
            if cont_ol == 0:  # Case i not overlapping
                if flag == 0:
                    # Add case
                    res_plags.append(plags[i])
                    res_psr.append(psr[i])
                else:
                    flag = 0
                i += 1
            else:  # Case i overlapping
                ind_max = i
                higher_sim = 0.0
                for j in range(1, cont_ol + 1):  # For every overlapping case j
                    if flag == 0:
                        sents_i = range(plags[i][0][0], plags[i][0][1] + 1)  # sents of case i in doc1
                        range_i = range(plags[i][1][0], plags[i][1][1] + 1)  # sents of case i in doc2
                    else:
                        sents_i = range(res_plags[-1][0][0],
                                        res_plags[-1][0][1] + 1)  # sents of last added case in doc1
                        range_i = range(res_plags[-1][1][0],
                                        res_plags[-1][1][1] + 1)  # sents of last added case in doc2
                    sents_j = range(plags[i + j][0][0], plags[i + j][0][1] + 1)  # sents of case j in doc1
                    sim_i_ol = 0.0
                    sim_j_ol = 0.0
                    sim_i_nol = 0.0
                    sim_j_nol = 0.0
                    cont_ol_sents = 0
                    cont_i_nol_sents = 0
                    cont_j_nol_sents = 0
                    for sent in sents_i:  # For each sent of last added case in doc1
                        sim_max = 0.0
                        for k in range_i:  # For each sent of last added case in doc2
                            sim = cosine_measure(susp_bow[sent], src_bow[k])
                            if sim > sim_max:
                                sim_max = sim  # Find most similar sentence
                        if sent in sents_j:  # If in sents of case j in doc1 (=> overlapping)
                            sim_i_ol += sim_max
                            cont_ol_sents += 1
                        else:
                            sim_i_nol += sim_max
                            cont_i_nol_sents += 1
                    range_j = range(plags[i + j][1][0], plags[i + j][1][1] + 1)  # sents of case j in doc2
                    for sent in sents_j:  # For each sent of case j in doc1
                        sim_max = 0.0
                        for k in range_j:  # For each sent of case j in doc2
                            sim = cosine_measure(susp_bow[sent], src_bow[k])
                            if sim > sim_max:
                                sim_max = sim  # Find most similar sentence
                        if sent in sents_i:  # if in sents of last added case
                            sim_j_ol += sim_max
                        else:
                            sim_j_nol += sim_max
                            cont_j_nol_sents += 1
                    sim_i = sim_i_ol / cont_ol_sents  # avg similarity of overlapping sents
                    if cont_i_nol_sents != 0:
                        sim_i = sim_i + (1 - sim_i) * sim_i_nol / float(cont_i_nol_sents)  # formula (1), quality of P
                    sim_j = sim_j_ol / cont_ol_sents
                    if cont_j_nol_sents != 0:
                        sim_j = sim_j + (1 - sim_j) * sim_j_nol / float(cont_j_nol_sents)  # formula (1), quality of Q
                    if sim_i > 0.99 and sim_j > 0.99:  # If both very similar
                        if len(sents_j) > len(sents_i):  # Chose the longer case
                            if sim_j > higher_sim:  # Store index and sim if no other more similar overlapping case j
                                # exists
                                ind_max = i + j
                                higher_sim = sim_j
                        else:
                            if sim_i > higher_sim:
                                ind_max = i
                                higher_sim = sim_i
                    elif sim_j > sim_i:  # Otherwise store most similar
                        if sim_j > higher_sim:
                            ind_max = i + j
                            higher_sim = sim_j
                        elif sim_i > higher_sim:
                            ind_max = i
                            higher_sim = sim_i
                if flag == 0:  # If last case i not overlapping, then add best case from P union psi(P)
                    res_plags.append(plags[ind_max])
                    res_psr.append(psr[ind_max])
                elif ind_max != i:  # If last case i overlapped and better case found now
                    del res_plags[-1]
                    del res_psr[-1]
                    res_plags.append(plags[ind_max])
                    res_psr.append(psr[ind_max])
                i = i + cont_ol  # Go to last overlapping case
                flag = 1  # Set overlapping case flag
        return res_plags, res_psr

    def remove_small_plags(self, plags, psr, src_offsets, susp_offsets, th):
        """
        DESCRIPTION: Remove the plagiarism cases that have less tha th characters either in the source or suspicios
        fragments
        INPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Have the plagiarism cases represented by
        min
        and max sentence index in suspicious and source document respectively
               psr <list of list of tuples (int, int)> - Contains the clusters
               src_offsets <list of tuples (int, int)> - Contain the char offset and length of each source document
               sentence
               susp_offsets <list of tuples (int, int)> - Contain the char offset and length of each suspicious document
               sentence
        OUTPUT: res_plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases without
        short cases
                res_psr <list of list of tuples (int, int)> - Contains the clusters without short cases
        """
        res_plags = []
        res_psr = []
        for i in range(len(plags)):  # For each case
            # First char of first sentence of case in susp, first char of last sent of case in susp
            # + length of last sent in susp doc
            arg1 = (susp_offsets[plags[i][0][0]][0], susp_offsets[plags[i][0][1]][0] + susp_offsets[plags[i][0][1]][1])
            # Same for src
            arg2 = (src_offsets[plags[i][1][0]][0], src_offsets[plags[i][1][1]][0] + src_offsets[plags[i][1][1]][1])
            if arg1[1] - arg1[0] >= th and arg2[1] - arg2[0] >= th:  # only append if char num >= min_sentlen
                res_plags.append(plags[i])
                res_psr.append(psr[i])
        return res_plags, res_psr
