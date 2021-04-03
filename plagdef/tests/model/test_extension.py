from collections import Counter
from itertools import combinations
from random import randint
from unittest.mock import patch

from pytest import mark

from plagdef.model.extension import SeedExtender, Cluster
from plagdef.model.legacy.extension import LegacySeedExtender
from plagdef.model.models import Sentence
from plagdef.model.preprocessing import Document
from plagdef.model.seeding import Seed


def test_clusters_are_equal():
    cluster1 = Cluster(set(_create_seeds([(0, 0), (3, 1)])))
    cluster2 = Cluster(set(_create_seeds([(3, 1), (0, 0)])))
    assert cluster1 == cluster2


def test_cluster_sets_are_equal():
    cluster1 = Cluster(set(_create_seeds([(0, 0), (3, 1)])))
    cluster2 = Cluster(set(_create_seeds([(3, 1), (0, 0)])))
    assert {cluster1, cluster2} == {cluster2, cluster1}


def test_clustering_with_no_seeds():
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(), 4)
    assert clusters == set()


def test_clustering_with_equal_clusters():
    # The given seeds form these clusters:
    # doc1: [[s0, s1], [s2, s3]]
    # doc2: [[s0, s1], [s2, s3]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = _create_seeds([(0, 0), (3, 1), (9, 7), (10, 9)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster({seeds[0], seeds[1]}), Cluster({seeds[2], seeds[3]})}


def test_clustering_with_more_clusters_in_doc1():
    # The given seeds form these clusters:
    # doc1: [[s0, s1], [s2]]
    # doc2: [[s0, s1, s2]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = _create_seeds([(0, 0), (3, 1), (9, 6)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster({seeds[0], seeds[1]}), Cluster({seeds[2]})}


def test_clustering_with_more_clusters_in_doc2():
    # The given seeds form these clusters:
    # doc1: [[s0, s1, s2]]
    # doc2: [[s0, s1], [s2]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = _create_seeds([(0, 0), (3, 1), (7, 8)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster({seeds[0], seeds[1]}), Cluster({seeds[2]})}


def test_clustering_with_totally_different_clusters():
    # The given seeds form these clusters:
    # doc1: [[s0, s1, s2, s3]]
    # doc2: [[s0], [s1], [s2], [s3]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = _create_seeds([(0, 0), (3, 6), (5, 12), (7, 18)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster({seeds[0]}), Cluster({seeds[1]}),
                        Cluster({seeds[2]}), Cluster({seeds[3]})}


def test_clustering_with_seed_which_is_part_of_different_clusters():
    # doc1: [[s0], [s1, s2], [s3], [s4]]
    # doc2: [[s0], [s1], [s2, s3], [s4]]
    seeds = _create_seeds([(18, 17), (36, 33), (37, 49), (54, 53), (74, 63)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster({seeds[0]}), Cluster({seeds[1]}), Cluster({seeds[2]}),
                        Cluster({seeds[3]}), Cluster({seeds[4]})}


def test_clustering_with_three_seeds_in_cluster():
    # doc1: [[s0], [s1, s2, s3], [s4]]
    # doc2: [[s0], [s1], [s2, s3], [s4]]
    seeds = _create_seeds([(2, 17), (21, 34), (25, 43), (30, 45), (50, 51)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster({seeds[0]}), Cluster({seeds[1]}),
                        Cluster({seeds[2], seeds[3]}), Cluster({seeds[4]})}


def test_clustering_processing_order_is_important():
    # doc1: [[s0, s1, s2], [s3, s4, s5]]
    # doc2: [[s0, s1], [s2, s3], [s4, s5]]
    seeds = _create_seeds([(4, 0), (7, 2), (10, 12), (19, 14), (21, 23), (26, 28)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster({seeds[0], seeds[1]}),
                        Cluster({seeds[2]}), Cluster({seeds[3]}),
                        Cluster({seeds[4], seeds[5]})}


def test_clustering_seed_order_makes_no_difference():
    # doc1: [[s0, s1]]
    # doc2: [[s1, s0]]
    seeds = _create_seeds([(0, 4), (5, 1)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster({seeds[0], seeds[1]})}


@mark.skip(reason="Takes quite long and was just used to generate test cases.")
def test_compare_clustering_with_legacy():
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    legacy_extender = LegacySeedExtender()
    docs = [Document(f'doc{i}', '') for i in range(1, 11)]
    for doc1, doc2 in combinations(docs, 2):
        doc1_idx = doc2_idx = -1
        seed_tpls = []
        for i in range(100):
            doc1_idx, doc2_idx = randint(doc1_idx + 1, doc1_idx + 20), randint(doc2_idx, doc2_idx + 10)
            seed_tpls.append((doc1_idx, doc2_idx))
        seeds = _create_seeds(seed_tpls)
        clusters = extender._cluster(set(seeds), 4)
        leg_clusters = legacy_extender._clustering(
            [(seed.sent1.idx, seed.sent2.idx, seed.cos_sim, seed.dice_sim) for seed in seeds],
            None, None, 4, 4, 1, 1, 0, 0)
        conv_leg_clusters = set()
        for cluster in leg_clusters:
            cluster_seed_tpls = []
            [cluster_seed_tpls.append((seed[0], seed[1])) for seed in cluster]
            cluster_seeds = _create_seeds(cluster_seed_tpls)
            conv_leg_clusters.add(Cluster(set(cluster_seeds)))
        assert clusters == conv_leg_clusters


def test_filter_with_only_similar_clusters():
    seeds = _create_seeds([(0, 2), (2, 4), (10, 5), (11, 7), (14, 11)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    # Calculation of cluster similarity untested
    with patch('plagdef.model.models.util.cos_sim') as cos_sim:
        cos_sim.return_value = 1
        clusters = [Cluster({seeds[0], seeds[1]}),
                    Cluster({seeds[2], seeds[3], seeds[4]})]
        filtered_clusters = extender._filter(set(clusters), 4)
    assert filtered_clusters == {clusters[0], clusters[1]}


def test_filter_with_cluster_with_similarity_below_th():
    seeds = _create_seeds([(0, 2)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    # Calculation of cluster similarity untested
    with patch('plagdef.model.models.util.cos_sim') as cos_sim:
        cos_sim.return_value = 0
        clusters = [Cluster({seeds[0]})]
        filtered_clusters = extender._filter(set(clusters), 4)
    assert filtered_clusters == set()


def test_filter_with_cluster_which_is_reduced():
    seeds = _create_seeds([(0, 5), (1, 7), (6, 11)])
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    # Calculation of cluster similarity untested
    with patch('plagdef.model.models.util.cos_sim') as cos_sim:
        # idx 0: Create list 'clusters' with one cluster and cos_sim = 0
        # idx 1-3: doc1_clusters: Cluster({seeds[0], seeds[1]}), Cluster({seeds[2]})
        # idx 4-6: Check if doc1_clusters are possible in doc2: Cluster({seeds[0], seeds[1]}), Cluster({seeds[2]})
        # idx 7-8: Create list 'expected_clusters' with two clusters and cos_sim = 1
        cos_sim.side_effect = [0, 1, 1, 1, 1, 1, 1]
        clusters = [Cluster({seeds[0], seeds[1], seeds[2]})]
        filtered_detections = extender._filter(set(clusters), 4)
        expected_clusters = {Cluster({seeds[0], seeds[1]}), Cluster({seeds[2]})}
    assert filtered_detections == expected_clusters


def _create_seeds(seed_tpls: list[tuple]):
    doc1, doc2 = Document('doc1', ''), Document('doc2', '')
    max_idx_doc1, max_idx_doc2 = max(seed_tpls, key=lambda seed: seed[0]), \
                                 max(seed_tpls, key=lambda seed: seed[1])
    [doc1.sents.add(Sentence(doc1, idx, -1, Counter(), {})) for idx in range(max_idx_doc1[0] + 1)]
    [doc2.sents.add(Sentence(doc2, idx, -1, Counter(), {})) for idx in range(max_idx_doc2[1] + 1)]
    seeds = []
    for seed_tpl in seed_tpls:
        seeds.append(Seed(doc1.sents[seed_tpl[0]], doc2.sents[seed_tpl[1]], 1, 1))
    return seeds
