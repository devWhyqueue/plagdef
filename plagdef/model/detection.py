from __future__ import annotations

import logging
from itertools import combinations

from tqdm import tqdm

from plagdef.model.extension import ClusterBuilder
from plagdef.model.filtering import ClusterFilter
from plagdef.model.models import Document, Match, DocumentPairMatches, Cluster, Fragment
from plagdef.model.preprocessing import Preprocessor
from plagdef.model.seeding import SeedFinder

log = logging.getLogger(__name__)


class DocumentMatcher:
    def __init__(self, config: dict):
        self._preprocessor = Preprocessor(config['min_sent_len'], config['rem_stop_words'])
        self._seeder = SeedFinder(config['min_cos_sim'], config['min_dice_sim'])
        self._extender = ClusterBuilder(config['adjacent_sents_gap'], config['min_adjacent_sents_gap'],
                                        config['min_sent_number'], config['min_cluster_cos_sim'])
        self._cluster_filter = ClusterFilter(config['min_cluster_char_len'])
        self._adjacent_sents_gap_summary = config['adjacent_sents_gap_summary']
        self._min_verbatim_match_char_len = config['min_verbatim_match_char_len']

    def find_matches(self, lang: str, docs: list[Document], common_docs=None) -> set[DocumentPairMatches]:
        self._preprocessor.preprocess(lang, docs, common_docs)
        log.info(f'Looking for matches in all pairs of {len(docs)} documents...')
        matches = set()
        doc_combs = set(combinations(docs, 2))
        for idx, (doc1, doc2) in enumerate(tqdm(doc_combs)):
            seeds = self._seeder.seed(doc1, doc2)
            clusters = self._extender.extend(seeds)
            clusters = self._cluster_filter.filter(clusters)
            verbatim_matches = self._verbatim_matches(clusters)
            if len(verbatim_matches):  # Plagiarism type: verbatim
                matches.add(DocumentPairMatches(verbatim_matches))
            else:
                summary_clusters = self._extender.extend(seeds, self._adjacent_sents_gap_summary)
                summary_clusters = self._cluster_filter.filter(summary_clusters)
                if len(summary_clusters):
                    sum_cluster_len_doc1, sum_cluster_len_doc2 = \
                        tuple(map(sum, zip(*(cluster.char_lengths() for cluster in summary_clusters))))

                    if sum_cluster_len_doc1 >= 3 * sum_cluster_len_doc2 \
                        or sum_cluster_len_doc2 >= 3 * sum_cluster_len_doc1:  # Plagiarism type: summary
                        matches.add(DocumentPairMatches({Match.from_cluster(cluster) for cluster in summary_clusters}))
                    elif len(clusters):  # Plagiarism type: intelligent
                        matches.add(DocumentPairMatches({Match.from_cluster(cluster) for cluster in clusters}))
        return matches

    def _verbatim_matches(self, clusters: set[Cluster]) -> set[Match]:
        matches = set()
        for cluster in clusters:
            cluster_matches = self._common_words(cluster)
            matches.update(self._resolve_overlaps(cluster_matches))
        return matches

    def _common_words(self, cluster: Cluster) -> set[Match]:
        verbatim_matches = set()
        frag1_words = [word for sent_words in [sent.words for sent in cluster.sents_doc1] for word in sent_words]
        frag2_words = [word for sent_words in [sent.words for sent in cluster.sents_doc2] for word in sent_words]
        lookup = [[0 for _ in range(len(frag2_words) + 1)] for _ in range(len(frag1_words) + 1)]
        for i in range(1, len(frag1_words) + 1):
            for j in range(1, len(frag2_words) + 1):
                if frag1_words[i - 1].text.lower() == frag2_words[j - 1].text.lower():
                    lookup[i][j] = lookup[i - 1][j - 1] + 1
                    match_char_len = sum([len(word) for word in frag1_words[i - lookup[i][j]:i]])
                    if match_char_len >= self._min_verbatim_match_char_len:
                        frag1_first, frag2_first = i - lookup[i][j], j - lookup[i][j]
                        frag1 = Fragment(frag1_words[frag1_first].start_char, frag1_words[i - 1].end_char, cluster.doc1)
                        frag2 = Fragment(frag2_words[frag2_first].start_char, frag2_words[j - 1].end_char, cluster.doc2)
                        verbatim_matches.add(Match(frag1, frag2))
        return verbatim_matches

    def _resolve_overlaps(self, matches: set[Match]) -> set[Match]:
        non_ol_matches = set()
        for match in sorted(matches, key=len, reverse=True):
            if not any(match.overlaps_with(non_ol_match) for non_ol_match in non_ol_matches):
                non_ol_matches.add(match)
        return non_ol_matches
