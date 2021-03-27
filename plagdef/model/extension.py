from __future__ import annotations

from dataclasses import dataclass

from plagdef.model.seeding import Seed
from plagdef.model.util import cos_sim, adjacent, cluster_tf_isf_bow


class SeedExtender:
    def __init__(self, adjacent_sents_gap: int, min_adjacent_sents_gap: int,
                 min_sent_number: int, min_cluster_cos_sim: float):
        self._adjacent_sents_gap = adjacent_sents_gap
        self._min_adjacent_sents_gap = min_adjacent_sents_gap
        self._min_sent_number = min_sent_number
        self._min_cluster_cos_sim = min_cluster_cos_sim

    def extend(self, seeds: set[Seed], adjacent_sents_gap: int = None) -> set[Detection]:
        if adjacent_sents_gap is None:
            adjacent_sents_gap = self._adjacent_sents_gap
        clusters = self._cluster(seeds, adjacent_sents_gap)
        return self._filter(clusters, adjacent_sents_gap)

    def _cluster(self, seeds: set[Seed], adjacent_sents_gap: int) -> set[Cluster]:
        doc1_clusters = self._join_seeds(frozenset(seeds), adjacent_sents_gap, first=True)
        clusters = set()
        for cluster in doc1_clusters:
            clusters.update(self._join_seeds(cluster.seeds, adjacent_sents_gap, first=False))
        return clusters

    def _join_seeds(self, seeds: frozenset[Seed], adjacent_sents_gap: int, first: bool) -> set[Cluster]:
        sorted_seeds = sorted(seeds, key=lambda s: s.sent1.idx if first else s.sent2.idx)
        clusters = set()
        seed_iter: enumerate = enumerate(sorted_seeds)
        for seed_idx, seed in seed_iter:
            cluster_seeds = [seed]  # Cluster contains at least first seed
            for adj_seed in sorted_seeds[seed_idx + 1:]:  # For following seeds
                sent1 = cluster_seeds[-1].sent1 if first else cluster_seeds[-1].sent2
                sent2 = adj_seed.sent1 if first else adj_seed.sent2
                if adjacent(sent1, sent2, adjacent_sents_gap):  # If sent is adjacent, add seed
                    cluster_seeds.append(next(seed_iter)[1])
                else:
                    break  # Seeds are sorted by sent idx
            clusters.add(Cluster(frozenset(cluster_seeds)))
        return clusters

    def _filter(self, clusters: set[Cluster], adjacent_sents_gap: int) -> set[Detection]:
        detections = set()
        for cluster in clusters:
            cluster_tf_isf_bow_doc1 = cluster_tf_isf_bow(cluster.doc1, cluster.first_sent_idx(first=True),
                                                         cluster.last_sent_idx(first=True))
            cluster_tf_isf_bow_doc2 = cluster_tf_isf_bow(cluster.doc2, cluster.first_sent_idx(first=False),
                                                         cluster.last_sent_idx(first=False))
            cluster_cos_sim = cos_sim(cluster_tf_isf_bow_doc1, cluster_tf_isf_bow_doc2)
            if cluster_cos_sim > self._min_cluster_cos_sim:
                detections.add(Detection(cluster, cluster_cos_sim))
            elif adjacent_sents_gap > self._min_adjacent_sents_gap:
                cluster_detections = self.extend(set(cluster.seeds), adjacent_sents_gap - 1)
                detections.update(cluster_detections)
        return detections


@dataclass(frozen=True)
class Cluster:
    seeds: frozenset[Seed]

    @property
    def doc1(self):
        return list(self.seeds)[0].sent1.doc

    @property
    def doc2(self):
        return list(self.seeds)[0].sent2.doc

    def first_sent_idx(self, first: bool) -> int:
        return min([seed.sent1.idx for seed in self.seeds]) if first else min([seed.sent2.idx for seed in self.seeds])

    def last_sent_idx(self, first: bool) -> int:
        return max([seed.sent1.idx for seed in self.seeds]) if first else max([seed.sent2.idx for seed in self.seeds])

    def __repr__(self):
        if not len(self.seeds):
            return 'Cluster()'
        string = 'Cluster('
        for seed in self.seeds:
            string = string + f'{repr(seed)}, '
        return f'{string[:-2]})'


@dataclass(frozen=True)
class Detection:
    cluster: Cluster
    cos_sim: float
