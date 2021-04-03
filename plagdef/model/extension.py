from __future__ import annotations

from plagdef.model.models import Seed, Cluster, Document


class SeedExtender:
    def __init__(self, doc1: Document, doc2: Document, adjacent_sents_gap: int, min_adjacent_sents_gap: int,
                 min_sent_number: int, min_cluster_cos_sim: float):
        # TODO: Just for compatibility
        self._doc1 = doc1
        self._doc2 = doc2
        self._adjacent_sents_gap = adjacent_sents_gap
        self._min_adjacent_sents_gap = min_adjacent_sents_gap
        self._min_sent_number = min_sent_number
        self._min_cluster_cos_sim = min_cluster_cos_sim

    # TODO: Just for compatibility
    def extend(self, leg_obj, seeds):
        seeds_new = set()
        for seed in seeds:
            sent1 = list(filter(lambda s: s.idx == seed[0], self._doc1.sents))[0]
            sent2 = list(filter(lambda s: s.idx == seed[1], self._doc2.sents))[0]
            seeds_new.add(Seed(sent1, sent2, seed[2], seed[3]))
        clusters = self.extend_new(seeds_new)
        leg_det = [[(cluster.sents_doc1[0].idx, cluster.sents_doc1[-1].idx),
                    (cluster.sents_doc2[0].idx, cluster.sents_doc2[-1].idx)] for cluster in clusters]
        leg_clusters = []
        for cluster in clusters:
            leg_clusters.append([(cluster.sents_doc1[0].idx, cluster.sents_doc2[0].idx,
                                  seed.cos_sim, seed.dice_sim)
                                 for seed in cluster.seeds])
        frag_sims = [cluster.cos_sim for cluster in clusters]
        return leg_det, leg_clusters, frag_sims

    def extend_new(self, seeds: set[Seed], adjacent_sents_gap: int = None) -> set[Cluster]:
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
        sorted_seeds = sorted(seeds, key=lambda s: s.sent1.start_char if first else s.sent2.start_char)
        clusters = set()
        seed_iter: enumerate = enumerate(sorted_seeds)
        for seed_idx, seed in seed_iter:
            cluster_seeds = [seed]  # Cluster contains at least first seed
            for adj_seed in sorted_seeds[seed_idx + 1:]:  # For following seeds
                sent1 = cluster_seeds[-1].sent1 if first else cluster_seeds[-1].sent2
                sent2 = adj_seed.sent1 if first else adj_seed.sent2
                if sent1.adjacent_to(sent2, adjacent_sents_gap):  # If sent is adjacent, add seed
                    cluster_seeds.append(next(seed_iter)[1])
                else:
                    break  # Seeds are sorted by sent start_char
            clusters.add(Cluster(set(cluster_seeds)))
        return clusters

    def _filter(self, clusters: set[Cluster], adjacent_sents_gap: int) -> set[Cluster]:
        filtered_clusters = set()
        for cluster in clusters:
            if cluster.cos_sim > self._min_cluster_cos_sim:
                filtered_clusters.add(cluster)
            elif adjacent_sents_gap > self._min_adjacent_sents_gap:
                cluster_detections = self.extend_new(set(cluster.seeds), adjacent_sents_gap - 1)
                filtered_clusters.update(cluster_detections)
        return filtered_clusters
