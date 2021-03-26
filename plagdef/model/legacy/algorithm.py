from __future__ import annotations

import math
import string
from dataclasses import dataclass
from itertools import combinations

import nltk

from plagdef.model.legacy.extension import LegacySeedExtender
from plagdef.model.preprocessing import Document, Preprocessor
from plagdef.model.seeding import Seeder


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


def remove_overlap3(plags, psr, src_bow, susp_bow):
    """
    DESCRIPTION: From a set of overlapping plagiarism cases, looking only on the suspicious side, selects the best
    case. See article (1) at the beggining of this file, for the formal description.
    INPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Have the plagiarism cases represented by min
    and max sentence index in suspicious and source document respectively
           psr <list of list of tuples (int, int)> - Contains the clusters
           src_bow <list of dictionaries> - Bag of words representing each sentence vector of source document
           susp_bow <list of dictionaries> - Bag of words representing each sentence vector of suspicious document
    OUTPUT: res_plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases without
    overlapping
            res_psr <list of list of tuples (int, int)> - Contains the clusters without overlapping
    """
    if len(plags) != 0:
        plags, psr = map(list, zip(*sorted(zip(plags, psr), key=lambda tup: tup[0][0][0])))
    res_plags = []
    res_psr = []
    flag = 0
    i = 0
    while i < len(plags):
        cont_ol = 0
        if flag == 0:
            for k in range(i + 1, len(plags)):
                if plags[k][0][0] - plags[i][0][1] <= 0:
                    cont_ol += 1
        else:
            for k in range(i + 1, len(plags)):
                if plags[k][0][0] - res_plags[-1][0][1] <= 0:
                    cont_ol += 1
        if cont_ol == 0:
            if flag == 0:
                res_plags.append(plags[i])
                res_psr.append(psr[i])
            else:
                flag = 0
            i += 1
        else:
            ind_max = i
            higher_sim = 0.0
            for j in range(1, cont_ol + 1):
                if flag == 0:
                    sents_i = range(plags[i][0][0], plags[i][0][1] + 1)
                    range_i = range(plags[i][1][0], plags[i][1][1] + 1)
                else:
                    sents_i = range(res_plags[-1][0][0], res_plags[-1][0][1] + 1)
                    range_i = range(res_plags[-1][1][0], res_plags[-1][1][1] + 1)
                sents_j = range(plags[i + j][0][0], plags[i + j][0][1] + 1)
                sim_i_ol = 0.0
                sim_j_ol = 0.0
                sim_i_nol = 0.0
                sim_j_nol = 0.0
                cont_ol_sents = 0
                cont_i_nol_sents = 0
                cont_j_nol_sents = 0
                for sent in sents_i:
                    sim_max = 0.0
                    for k in range_i:
                        sim = cosine_measure(susp_bow[sent], src_bow[k])
                        if sim > sim_max:
                            sim_max = sim
                    if sent in sents_j:
                        sim_i_ol += sim_max
                        cont_ol_sents += 1
                    else:
                        sim_i_nol += sim_max
                        cont_i_nol_sents += 1
                range_j = range(plags[i + j][1][0], plags[i + j][1][1] + 1)
                for sent in sents_j:
                    sim_max = 0.0
                    for k in range_j:
                        sim = cosine_measure(susp_bow[sent], src_bow[k])
                        if sim > sim_max:
                            sim_max = sim
                    if sent in sents_i:
                        sim_j_ol += sim_max
                    else:
                        sim_j_nol += sim_max
                        cont_j_nol_sents += 1
                sim_i = sim_i_ol / cont_ol_sents
                if cont_i_nol_sents != 0:
                    sim_i = sim_i + (1 - sim_i) * sim_i_nol / float(cont_i_nol_sents)
                sim_j = sim_j_ol / cont_ol_sents
                if cont_j_nol_sents != 0:
                    sim_j = sim_j + (1 - sim_j) * sim_j_nol / float(cont_j_nol_sents)
                if sim_i > 0.99 and sim_j > 0.99:
                    if len(sents_j) > len(sents_i):
                        if sim_j > higher_sim:
                            ind_max = i + j
                            higher_sim = sim_j
                    else:
                        if sim_i > higher_sim:
                            ind_max = i
                            higher_sim = sim_i
                elif sim_j > sim_i:
                    if sim_j > higher_sim:
                        ind_max = i + j
                        higher_sim = sim_j
                    elif sim_i > higher_sim:
                        ind_max = i
                        higher_sim = sim_i
            if flag == 0:
                res_plags.append(plags[ind_max])
                res_psr.append(psr[ind_max])
            elif ind_max != i:
                del res_plags[-1]
                del res_psr[-1]
                res_plags.append(plags[ind_max])
                res_psr.append(psr[ind_max])
            i = i + cont_ol
            flag = 1
    return res_plags, res_psr


def remove_small_plags(plags, psr, src_offsets, susp_offsets, th):
    """
    DESCRIPTION: Remove the plagiarism cases that have less tha th characters either in the source or suspicios
    fragments
    INPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Have the plagiarism cases represented by min
    and max sentence index in suspicious and source document respectively
           psr <list of list of tuples (int, int)> - Contains the clusters
           src_offsets <list of tuples (int, int)> - Contain the char offset and length of each source document sentence
           susp_offsets <list of tuples (int, int)> - Contain the char offset and length of each suspicious document
           sentence
    OUTPUT: res_plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases without
    short cases
            res_psr <list of list of tuples (int, int)> - Contains the clusters without short cases
    """
    res_plags = []
    res_psr = []
    for i in range(len(plags)):
        arg1 = (susp_offsets[plags[i][0][0]][0], susp_offsets[plags[i][0][1]][0] + susp_offsets[plags[i][0][1]][1])
        arg2 = (src_offsets[plags[i][1][0]][0], src_offsets[plags[i][1][1]][0] + src_offsets[plags[i][1][1]][1])
        if arg1[1] - arg1[0] >= th and arg2[1] - arg2[0] >= th:
            res_plags.append(plags[i])
            res_psr.append(psr[i])
    return res_plags, res_psr


def word_span_tokenizer(text):
    """
    DESCRIPTION: Tokenize a text in words
    INPUT: text <string> - Text to be tokenized
    OUTPUT: words <list> - List of words from text
            offsets <list of tuple (int, int)> - Initial and final position of each word
    """
    words = []
    offsets = []
    sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
    word_detector = nltk.TreebankWordTokenizer()
    punctuation = string.punctuation
    for span in sent_detector.span_tokenize(text):
        sent = text[span[0]:span[1]].lower()
        sent_words = []
        for token in word_detector.tokenize(sent):
            for char in token:
                if char not in punctuation:
                    sent_words.append(token)
                    break
        idx = 0
        for word in sent_words:
            words.append(word)
            pos = sent[idx:].find(word)
            offsets.append([span[0] + idx + pos, idx + span[0] + pos + len(word)])  # (Initial position, Final position)
            if idx == 0:  # changing first word offset
                offsets[-1][0] = span[0]
            idx = idx + pos + len(word)
        if len(words) > 0:  # Changing last word offset
            offsets[-1][1] = span[1]
    return words, offsets


# Using Dynamic programming to find all elements greater then th (not only biggest element)
def longest_common_substring_all(s1, s1_off, s2, s2_off, th):
    """
    DESCRIPTION: Find the common subtrings using dynamic programming
    INPUT: s1 <list> - List of words from text 1
           s1_off <list of tuple (int, int)> - List of offsets of text1
           s2 <list> - List of words from text 2
           s2_off <list of tuple (int, int)> - List of offsets of text2
           th <int> - Threshold in characters of shortest common substring allowed
    OUTPUT: res <list tuples (int, int, int, int)> - Common subtring correspondence in text1 and text2 represented as
    char offsets (t1_init, t1_end, t2_init, t2_end)
    """
    m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
    res = []
    longest, x_longest, y_longest = 0, 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
            else:
                m[x][y] = 0
                if m[x - 1][y - 1] != 0:
                    len_plag = s1_off[x - 2][1] - s1_off[x - 1 - m[x - 1][y - 1]][0]
                    if len_plag > th:
                        res.append((s1_off[x - 1 - m[x - 1][y - 1]][0], s1_off[x - 2][1],
                                    s2_off[y - 1 - m[x - 1][y - 1]][0], s2_off[y - 2][1]))
        if m[x][y] != 0:  # Last column
            len_plag = s1_off[x - 1][1] - s1_off[x - m[x][y]][0]
            if len_plag > th:
                res.append((s1_off[x - m[x][y]][0], s1_off[x - 1][1], s2_off[y - m[x][y]][0], s2_off[y - 1][1]))
    for y in range(1, len(s2)):  # Last row
        if m[-1][y] != 0:
            len_plag = s1_off[-1][1] - s1_off[len(s1_off) - m[-1][y]][0]
            if len_plag > th:
                res.append(
                    (s1_off[len(s1_off) - m[-1][y]][0], s1_off[- 1][1], s2_off[y - m[-1][y]][0], s2_off[y - 1][1]))
    return res


def common_substring_pro_all(str1, str2, th_acc):
    """
    DESCRIPTION: Find the common substrings longer than some threshold
    INPUT: str1 <list> - Text 1
           str2 <list> - Text 2
           th_acc <int> - Threshold in characters of shortest common substring allowed
    OUTPUT: res <list tuples (int, int, int, int)> - Common subtring correspondence in text1 and text2 represented as
    char offsets (t1_init, t1_end, t2_init, t2_end)
    """
    X, X_off = word_span_tokenizer(str1)
    Y, Y_off = word_span_tokenizer(str2)
    res = longest_common_substring_all(X, X_off, Y, Y_off, th_acc)
    return res


def verbatim_det_lcs_all(plags, psr, susp_text, src_text, susp_offsets, src_offsets, th_shortest):
    """
    DESCRIPTION: Uses longest common substring algorithm to classify a pair of documents being compared as verbatim
    plagarism candidate (the pair of documents), and removing the none verbatim cases if positive
    INPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Have the plagiarism cases represented by min
    and max sentence index in suspicious and source document respectively
           psr <list of list of tuples (int, int)> - Contains the clusters
           susp_text <string> - Suspicios document text
           src_text <string> - Source document text
           susp_offsets <list of tuples (int, int)> - Contain the char offset and length of each suspicious document
           sentence
           src_offsets <list of tuples (int, int)> - Contain the char offset and length of each source document sentence
           th_shortest <int> - Threshold in characters of shortest common substring allowed
    OUTPUT: res_plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases as common
    substrings or the same as the arguments depending on type_plag
            res_psr <list of list of tuples (int, int)> - Contains the clusters with seeds present in the common
            substrings, or the same as the arguments depending on type_plag
            type_plag <0 or 1> - 1: verbatim plagiarism case    0: Other plagiarism case
            res_long_frag <list> - Contains the lengths of common substrings
    """
    # plags[[(susp_ini, susp_end), (src_ini, src_end)], ...]
    res_plags = []
    res_psr = []
    res_long_frag = []
    i = 0
    type_plag = 0  # 0: Unknown, 1: no-obfuscation
    while i < len(plags):  # For each plagiarism case
        # print('Case',i)
        # print('Plag case', plags[i])
        # print('Seeds', psr[i])
        # sentences in seeds and those not in seeds
        res2 = common_substring_pro_all(susp_text[susp_offsets[plags[i][0][0]][0]: susp_offsets[plags[i][0][1]][0] +
                                                                                   susp_offsets[plags[i][0][1]][1]],
                                        src_text[src_offsets[plags[i][1][0]][0]: src_offsets[plags[i][1][1]][0] +
                                                                                 src_offsets[plags[i][1][1]][1]],
                                        th_shortest)
        res = []
        # Remove overlapping
        for tup_i in res2:
            flag = 0
            for tup_j in res2:
                if tup_i != tup_j and tup_i[2] >= tup_j[2] and tup_i[3] <= tup_j[3]:
                    flag = 1
                    break
            if flag == 0:
                res.append(tup_i)

        if len(res) > 0:
            if type_plag == 1:
                # Removing seeds with lcs shorter than th_shortest
                for sub_case in res:
                    res_plags.append(
                        [(susp_offsets[plags[i][0][0]][0] + sub_case[0], susp_offsets[plags[i][0][0]][0] + sub_case[1]),
                         (src_offsets[plags[i][1][0]][0] + sub_case[2], src_offsets[plags[i][1][0]][0] + sub_case[3])])
                    res_psr.append(psr[i])
                    res_long_frag.append(max([sub_case[1] - sub_case[0], sub_case[3] - sub_case[2]]))
            else:
                # Type 02-no-obfuscation detected. Starting over! Removing previously added cases!
                type_plag = 1
                res_plags = []
                res_psr = []
                res_long_frag = []
                for sub_case in res:
                    res_plags.append(
                        [(susp_offsets[plags[i][0][0]][0] + sub_case[0], susp_offsets[plags[i][0][0]][0] + sub_case[1]),
                         (src_offsets[plags[i][1][0]][0] + sub_case[2], src_offsets[plags[i][1][0]][0] + sub_case[3])])
                    res_psr.append(psr[i])
                    res_long_frag.append(max([sub_case[1] - sub_case[0], sub_case[3] - sub_case[2]]))
                # i = -1
        else:
            if type_plag != 1:
                res_plags.append(plags[i])
                res_psr.append(psr[i])
                res_long_frag.append(-1)
        i += 1
    return res_plags, res_psr, type_plag, res_long_frag


"""
MAIN CLASS
"""


class SGSPLAG:
    def __init__(self, susp_text, src_text, config):
        self.__dict__.update(config)

        self.susp_text = susp_text
        self.src_text = src_text
        self.src_voc = {}
        self.susp_voc = {}
        self.src_offsets = []
        self.susp_offsets = []
        self.src_bow = {}
        self.susp_bow = {}
        self.detections = None

    def process(self, preprocessor, sent_matcher, seed_extender):
        """
        DESCRIPTION: Process the plagiarism pipeline
        INPUT: self <SGSPLAG object>
        OUTPUT: type_plag <int> - Verbatim plagarism flag
                summary_flag <int> - Summary plagarism flag
        """
        preprocessor.preprocess(self)
        self.detections, type_plag, summary_flag = self.compare(sent_matcher, seed_extender)
        return type_plag, summary_flag

    def filtering(self, plags, psr):
        """
        DESCRIPTION: Filter the plagiarism cases by removing overlapping and short cases
        INPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases after
        validation
               psr <list of list of tuples (int, int)> - Contains the clusters after validation
        OUTPUT: plags <list of list of two tuples [(int, int), (int, int)]> - Contains the plagiarism cases. Also
        modify psr.
        """
        plags, psr = remove_overlap3(plags, psr, self.src_bow, self.susp_bow)
        plags, psr = remove_small_plags(plags, psr, self.src_offsets, self.susp_offsets, self.min_plaglen)

        return plags

    def compare(self, sent_matcher, seed_extender):
        """
        DESCRIPTION: Test a suspicious document for near-duplicate plagiarism with regards to a source document and
        return a feature list depending on the type_plag and summary_flag flags.
        INPUT: self <SGSPLAG object>
        OUTPUT: detections <list> - Representation of plagairism cases before writing the xml file with require PAN
        format
                type_plag <int> - Verbatim flag
                summary_flag <int> - Summary flag
        """
        detections = []
        ps = sent_matcher.seeding(self)
        plags, psr, sim_frag = seed_extender.extend(self, ps)
        plags = self.filtering(plags, psr)
        if self.verbatim != 0:
            plags_verbatim, psr_verbatim, type_plag, long_frag = verbatim_det_lcs_all(plags, psr, self.susp_text,
                                                                                      self.src_text, self.susp_offsets,
                                                                                      self.src_offsets,
                                                                                      self.verbatim_minlen)
        else:
            type_plag = 0

        ####META-CLASSIFIER####
        if self.summary != 0:
            self.src_gap = self.src_gap_summary
            self.susp_gap = self.susp_gap_summary
            plags2, psr2, sim_frag = seed_extender.extend(self, ps)
            plags2 = self.filtering(plags2, psr2)
        summary_flag = 0
        if type_plag == 0:
            sum_src = 0
            sum_susp = 0
            if self.summary != 0:
                for plag in plags2:
                    arg1 = (self.susp_offsets[plag[0][0]][0],
                            self.susp_offsets[plag[0][1]][0] + self.susp_offsets[plag[0][1]][1])
                    arg2 = (
                        self.src_offsets[plag[1][0]][0],
                        self.src_offsets[plag[1][1]][0] + self.src_offsets[plag[1][1]][1])
                    sum_susp = sum_susp + (arg1[1] - arg1[0])
                    sum_src = sum_src + (arg2[1] - arg2[0])
            if sum_src != 0 and sum_src >= 3 * sum_susp:  # Summary heuristic
                summary_flag = 1
                for plag in plags2:
                    arg1 = (self.susp_offsets[plag[0][0]][0],
                            self.susp_offsets[plag[0][1]][0] + self.susp_offsets[plag[0][1]][1])
                    arg2 = (
                        self.src_offsets[plag[1][0]][0],
                        self.src_offsets[plag[1][1]][0] + self.src_offsets[plag[1][1]][1])
                    detections.append([arg1, arg2])
            else:
                for plag in plags:
                    arg1 = (self.susp_offsets[plag[0][0]][0],
                            self.susp_offsets[plag[0][1]][0] + self.susp_offsets[plag[0][1]][1])
                    arg2 = (
                        self.src_offsets[plag[1][0]][0],
                        self.src_offsets[plag[1][1]][0] + self.src_offsets[plag[1][1]][1])
                    detections.append([arg1, arg2])
        else:
            for plag in plags_verbatim:
                arg1 = plag[0][0], plag[0][1]
                arg2 = plag[1][0], plag[1][1]
                detections.append([arg1, arg2])
        return detections, type_plag, summary_flag


@dataclass(frozen=True)
class Section:
    doc: Document
    offset: int
    length: int


@dataclass(frozen=True)
class Match:
    sec1: Section
    sec2: Section


class DifferentDocumentPairError(Exception):
    pass


class InvalidConfigError(Exception):
    pass


class DocumentPairMatches:
    def __init__(self):
        self._matches: list[Match] = []

    def add(self, match: Match):
        if self._matches:
            doc_pair1, doc_pair2 = (self._matches[-1].sec1.doc, self._matches[-1].sec2.doc), \
                                   (match.sec1.doc, match.sec2.doc)
            if not doc_pair1 == doc_pair2:
                raise DifferentDocumentPairError(f'Only matches of document pair {doc_pair1} can be added.')
        self._matches.append(match)

    @property
    def doc1(self) -> Document:
        if not self.empty():
            return self._matches[0].sec1.doc

    @property
    def doc2(self) -> Document:
        if not self.empty():
            return self._matches[0].sec2.doc

    def list(self) -> [Match]:
        return self._matches

    def empty(self) -> bool:
        return not self._matches


def find_matches(docs: list[Document], lang: str, config: dict) -> list[DocumentPairMatches]:
    matches = []
    try:
        preprocessor = Preprocessor(lang, config['min_sent_len'], config['rem_stop_words'])
        preprocessor.preprocess_new(docs)
        for doc1, doc2 in combinations(docs, 2):
            doc_pair_matches = DocumentPairMatches()
            sgsplag_obj = SGSPLAG(doc1.text, doc2.text, config)

            preprocessor.set_docs(doc1, doc2)
            sgsplag_obj.process(preprocessor, Seeder(config['th1'], config['th2']), LegacySeedExtender())

            for det in sgsplag_obj.detections:
                match = Match(Section(doc1, det[0][0], det[0][1] - det[0][0]),
                              Section(doc2, det[1][0], det[1][1] - det[1][0]))
                doc_pair_matches.add(match)
            if not doc_pair_matches.empty():
                matches.append(doc_pair_matches)
        return matches
    except (KeyError, AttributeError) as e:
        raise InvalidConfigError('The given config seems to be invalid.') from e
