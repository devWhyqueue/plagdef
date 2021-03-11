import copy
import math

import nltk
from Stemmer import Stemmer


class LegacyPreprocessor:
    def preprocess(self, legacy_obj):
        """
        DESCRIPTION: Preprocess the suspicious and source document
        INPUT: self <SGSPLAG object>
        OUTPUT: None. Gets bag of words with tf-idf, offsets and preprocess sentences
        """
        legacy_obj.src_bow = self._tokenize(legacy_obj.src_text, legacy_obj.src_voc,
                                            legacy_obj.src_offsets)
        self._join_small_sents(legacy_obj.src_bow, legacy_obj.src_offsets, legacy_obj.min_sent_len,
                               legacy_obj.src_voc)
        legacy_obj.susp_bow = self._tokenize(legacy_obj.susp_text, legacy_obj.susp_voc,
                                             legacy_obj.susp_offsets)
        self._join_small_sents(legacy_obj.susp_bow, legacy_obj.susp_offsets, legacy_obj.min_sent_len,
                               legacy_obj.susp_voc)

        self._tf_isf(legacy_obj.src_bow, legacy_obj.src_voc, legacy_obj.susp_bow,
                     legacy_obj.susp_voc)

    def _tokenize(self, text, voc={}, offsets=[], rem_sw=0):
        """
        DESCRIPTION: Tokenization and vectorization of sentences in a document
        INPUTS: text <string> - Text to be pre-processed
                voc <dictionary> - The keys are the types (vocabulary) in a document while the values are the sentence
                frequency
                offsets <2-tuple> - First value contains the offset character and the next contain the length in
                characters
                sents <list> - Sentences of the text without tokenization
                rem_sw <integer> - Option about treatment of stopwords (0): None stopword remove, (1): 50 more common
                stopwords removed, (other): All stopwords removed
        OUTPUT: sent_vects <list of dictionaries> - List of dictionaries representing each sentence vector. Sparce
        bag of
        words. Also modify sents, offsets and voc.
        NOTE: If char_preprocess() is used, you must use update_offsets() also
        """
        sents = []
        text = text.replace(chr(0), ' ')
        sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
        word_detector = nltk.TreebankWordTokenizer()
        stemmer = Stemmer('english')
        sent_spans = sent_detector.span_tokenize(text)
        sent_vects = []
        if rem_sw == 0:
            stopwords = []
        elif rem_sw == 1:
            stopwords = ['the', 'of', 'and', 'a', 'in', 'to', 'is', 'was', 'it', 'for', 'with', 'he', 'be', 'on', 'i',
                         'that', 'by', 'at', 'you', '\'s', 'are', 'not', 'his', 'this', 'from', 'but', 'had', 'which',
                         'she', 'they', 'or', 'an', 'were', 'we', 'their', 'been', 'has', 'have', 'will', 'would',
                         'her',
                         'n\'t', 'there', 'can', 'all', 'as', 'if', 'who', 'what', 'said']
        else:
            stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
                         'yourself',
                         'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
                         'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
                         'this',
                         'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
                         'has',
                         'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
                         'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
                         'between',
                         'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
                         'in',
                         'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
                         'when',
                         'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
                         'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', '\'s', 'n\'t',
                         'can', 'will', 'just', 'don', 'should', 'now']
        for span in sent_spans:  # For each sentence
            sents.append(text[span[0]: span[1]].lower())
            sent_dic = {}
            for word in word_detector.tokenize(sents[-1]):  # for each word in the sentence
                if word[0].isalnum() and len(word) > 2:
                    if word not in stopwords:
                        word_pp = stemmer.stemWord(word)  # if word not in stopwords_all else word (costly)
                    else:
                        word_pp = word
                else:
                    continue
                if word_pp in sent_dic:
                    sent_dic[word_pp] += 1
                else:  # only one time for each sentence, increase voc[word] value
                    sent_dic[word_pp] = 1
                    if word_pp in voc:
                        voc[word_pp] += 1
                    else:
                        voc[word_pp] = 1
            if len(sent_dic) > 0:
                sent_vects.append(sent_dic)
                offsets.append([span[0], span[1] - span[0]])
        return sent_vects

    def _join_small_sents(self, list_dic, offsets, min_sentlen, voc):
        """
        DESCRIPTION: Remove or annex sentences with less than a certain amount of words (min_sentlen)
        INPUTS: list_dic <list of dictionaries> - List containing the vectors (dictionaries) of a document
                offsets <2-tuple> - First value contains the offset character and the next contain the length in
                characters
                min_sentlen <integer> - Minimum of words allowed in a sentence
                rssent <integer> - Action to perform (0): Annex small sentences, (1) Remove small sentences
                voc <dictionary> - The keys are the types (vocabulary) in a document while the values are the sentence
                frequency
        OUTPUT: No returned value. Modify the inputs list_dic, offsets and voc
        """
        i = 0
        range_i = len(list_dic) - 1
        while i < range_i:
            if sum(list_dic[i].values()) < min_sentlen:
                for k in list_dic[i].keys():
                    if k in list_dic[i + 1]:
                        voc[k] -= 1
                list_dic[i + 1] = self._sum_vect(list_dic[i + 1], list_dic[i])
                del list_dic[i]
                offsets[i + 1] = (offsets[i][0], offsets[i + 1][1] + offsets[i][1])
                del offsets[i]
                range_i -= 1
            else:
                i = i + 1

    def _sum_vect(self, dic1, dic2):
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

    def _tf_isf(self, list_dic1, voc1, list_dic2, voc2):
        """
        DESCRIPTION: Compute the tf-idf <tf x ln(N/df)>  from a list of sentences with tf and the vocabularies in
        suspicios and source document
        INPUT: list_dic1 <list of dictionaries> -  List containing the vectors (dictionaries) of document 1
               voc1 <dictionary> - Vocabulary at document 1 with the idf of each one
               list_dic2 <list of dictionaries> -  List containing the vectors (dictionaries) of document 2
               voc2 <dictionary> - Vocabulary at document 2 with the idf of each one
        OUTPUT: No returned value. Modify the inputs list_dic1 and list_dic2
        """
        df = self._sum_vect(voc1, voc2)
        td = len(list_dic1) + len(list_dic2)
        for i in range(len(list_dic1)):
            for j in list_dic1[i].keys():
                list_dic1[i][j] *= math.log(td / float(df[j]))
        for i in range(len(list_dic2)):
            for j in list_dic2[i].keys():
                list_dic2[i][j] *= math.log(td / float(df[j]))
