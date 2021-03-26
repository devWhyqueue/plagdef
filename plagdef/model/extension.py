from __future__ import annotations

from dataclasses import dataclass

from plagdef.model.preprocessing import Sentence
from plagdef.model.seeding import Seed


class SeedExtender:
    def __init__(self, adjacent_sents_gap: int, min_sent_number: int):
        self._adjacent_sents_gap = adjacent_sents_gap
        self._min_sent_number = min_sent_number

    def extend(self, seeds: set[Seed]) -> set[Cluster]:
        doc1_clusters = self._cluster(frozenset(seeds), first=True)
        clusters = set()
        for cluster in doc1_clusters:
            clusters.update(self._cluster(cluster.seeds, first=False))
        return clusters

    def _cluster(self, seeds: frozenset[Seed], first: bool) -> set[Cluster]:
        sorted_seeds = sorted(seeds, key=lambda s: s.sent1.idx if first else s.sent2.idx)
        clusters = set()
        seed_iter: enumerate = enumerate(sorted_seeds)
        for seed_idx, seed in seed_iter:
            cluster_seeds = [seed]  # Cluster contains at least first seed
            for adj_seed in sorted_seeds[seed_idx + 1:]:  # For following seeds
                sent1 = cluster_seeds[-1].sent1 if first else cluster_seeds[-1].sent2
                sent2 = adj_seed.sent1 if first else adj_seed.sent2
                if self._adjacent(sent1, sent2):  # If sent is adjacent, add seed
                    cluster_seeds.append(next(seed_iter)[1])
                else:
                    break  # Seeds are sorted by sent idx
            clusters.add(Cluster(set(cluster_seeds)))
        return clusters

    def _adjacent(self, sent1: Sentence, sent2: Sentence) -> bool:
        return abs(sent1.idx - sent2.idx) - 1 <= self._adjacent_sents_gap


@dataclass(unsafe_hash=True)
class Cluster:
    def __init__(self, seeds: set[Seed]):
        self.seeds = frozenset(seeds)

    def __repr__(self):
        if not len(self.seeds):
            return 'Cluster()'
        string = 'Cluster('
        for seed in self.seeds:
            string = string + f'{repr(seed)}, '
        return f'{string[:-2]})'
