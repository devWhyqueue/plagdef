from collections import Counter
from itertools import combinations
from random import randint
from unittest.mock import patch

from plagdef.model.extension import SeedExtender, Cluster, Detection
from plagdef.model.legacy.extension import LegacySeedExtender
from plagdef.model.preprocessing import Document
from plagdef.model.seeding import Seed
from plagdef.tests.fakes import FakeSentence


def test_clusters_are_equal():
    cluster1 = Cluster(frozenset({_create_seed(0, 0), _create_seed(3, 1)}))
    cluster2 = Cluster(frozenset({_create_seed(3, 1), _create_seed(0, 0)}))
    assert cluster1 == cluster2


def test_cluster_sets_are_equal():
    cluster1 = Cluster(frozenset({_create_seed(0, 0), _create_seed(3, 1)}))
    cluster2 = Cluster(frozenset({_create_seed(3, 1), _create_seed(0, 0)}))
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
    seeds = [_create_seed(0, 0),
             _create_seed(3, 1),
             _create_seed(9, 7),
             _create_seed(10, 9)]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster(frozenset({seeds[0], seeds[1]})), Cluster(frozenset({seeds[2], seeds[3]}))}


def test_clustering_with_more_clusters_in_doc1():
    # The given seeds form these clusters:
    # doc1: [[s0, s1], [s2]]
    # doc2: [[s0, s1, s2]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = [_create_seed(0, 0),
             _create_seed(3, 1),
             _create_seed(9, 6)]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster(frozenset({seeds[0], seeds[1]})), Cluster(frozenset({seeds[2]}))}


def test_clustering_with_more_clusters_in_doc2():
    # The given seeds form these clusters:
    # doc1: [[s0, s1, s2]]
    # doc2: [[s0, s1], [s2]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = [_create_seed(0, 0),
             _create_seed(3, 1),
             _create_seed(7, 8)]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster(frozenset({seeds[0], seeds[1]})), Cluster(frozenset({seeds[2]}))}


def test_clustering_with_totally_different_clusters():
    # The given seeds form these clusters:
    # doc1: [[s0, s1, s2, s3]]
    # doc2: [[s0], [s1], [s2], [s3]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = [_create_seed(0, 0),
             _create_seed(3, 6),
             _create_seed(5, 12),
             _create_seed(7, 18)]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster(frozenset({seeds[0]})), Cluster(frozenset({seeds[1]})),
                        Cluster(frozenset({seeds[2]})), Cluster(frozenset({seeds[3]}))}


def test_clustering_with_seed_which_is_part_of_different_clusters():
    # doc1: [[s0], [s1, s2], [s3], [s4]]
    # doc2: [[s0], [s1], [s2, s3], [s4]]
    seeds = [_create_seed(18, 17), _create_seed(36, 33), _create_seed(37, 49),
             _create_seed(54, 53), _create_seed(74, 63)]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster(frozenset({seeds[0]})), Cluster(frozenset({seeds[1]})), Cluster(frozenset({seeds[2]})),
                        Cluster(frozenset({seeds[3]})), Cluster(frozenset({seeds[4]}))}


def test_clustering_with_three_seeds_in_cluster():
    # doc1: [[s0], [s1, s2, s3], [s4]]
    # doc2: [[s0], [s1], [s2, s3], [s4]]
    seeds = [_create_seed(2, 17), _create_seed(21, 34), _create_seed(25, 43),
             _create_seed(30, 45), _create_seed(50, 51)]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster(frozenset({seeds[0]})), Cluster(frozenset({seeds[1]})),
                        Cluster(frozenset({seeds[2], seeds[3]})), Cluster(frozenset({seeds[4]}))}


def test_clustering_processing_order_is_important():
    # doc1: [[s0, s1, s2], [s3, s4, s5]]
    # doc2: [[s0, s1], [s2, s3], [s4, s5]]
    seeds = [_create_seed(4, 0), _create_seed(7, 2),
             _create_seed(10, 12), _create_seed(19, 14),
             _create_seed(21, 23), _create_seed(26, 28)]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster(frozenset({seeds[0], seeds[1]})),
                        Cluster(frozenset({seeds[2]})), Cluster(frozenset({seeds[3]})),
                        Cluster(frozenset({seeds[4], seeds[5]}))}


def test_clustering_seed_order_makes_no_difference():
    # doc1: [[s0, s1]]
    # doc2: [[s1, s0]]
    seeds = [_create_seed(0, 4), _create_seed(5, 1)]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    clusters = extender._cluster(set(seeds), 4)
    assert clusters == {Cluster(frozenset({seeds[0], seeds[1]}))}


def test_compare_clustering_with_legacy():
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    legacy_extender = LegacySeedExtender()
    docs = [Document(f'doc{i}', '') for i in range(1, 11)]
    for doc1, doc2 in combinations(docs, 2):
        doc1_idx = doc2_idx = -1
        seeds = []
        for i in range(100):
            doc1_idx, doc2_idx = randint(doc1_idx + 1, doc1_idx + 20), randint(doc2_idx + 1, doc2_idx + 10)
            seeds.append(_create_seed(doc1_idx, doc2_idx, doc1.name, doc2.name))
        clusters = extender._cluster(set(seeds), 4)
        leg_clusters = legacy_extender._clustering(
            [(seed.sent1.idx, seed.sent2.idx, seed.cos_sim, seed.dice_sim) for seed in seeds],
            None, None, 4, 4, 1, 1, 0, 0)
        conv_leg_clusters = set()
        for cluster in leg_clusters:
            cluster_seeds = {_create_seed(seed[0], seed[1], doc1.name, doc2.name) for seed in cluster}
            conv_leg_clusters.add(Cluster(frozenset(cluster_seeds)))
        assert clusters == conv_leg_clusters


def test_filter_with_only_similar_clusters():
    clusters = [Cluster(frozenset({_create_seed(0, 2), _create_seed(2, 4)})),
                Cluster(frozenset({_create_seed(10, 5), _create_seed(11, 7), _create_seed(14, 11)}))]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    # Calculation of cluster similarity untested
    with patch('plagdef.model.extension.cluster_tf_isf_bow') as cluster_bow, \
        patch('plagdef.model.extension.cos_sim') as cos_sim:
        cluster_bow.return_value = {}
        cos_sim.return_value = 1
        filtered_detections = extender._filter(set(clusters), 4)
    assert filtered_detections == {Detection(clusters[0], 1), Detection(clusters[1], 1)}


def test_filter_with_cluster_with_similarity_below_th():
    clusters = [Cluster(frozenset({_create_seed(0, 2)}))]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    # Calculation of cluster similarity untested
    with patch('plagdef.model.extension.cluster_tf_isf_bow') as cluster_bow, \
        patch('plagdef.model.extension.cos_sim') as cos_sim:
        cluster_bow.return_value = {}
        cos_sim.return_value = 0
        filtered_detections = extender._filter(set(clusters), 4)
    assert filtered_detections == set()


def test_filter_with_cluster_which_is_reduced():
    clusters = [Cluster(frozenset({_create_seed(0, 5), _create_seed(1, 7), _create_seed(6, 11)}))]
    extender = SeedExtender(None, None, 4, 0, 1, 0.34)
    # Calculation of cluster similarity untested
    with patch('plagdef.model.extension.cluster_tf_isf_bow') as cluster_bow, \
        patch('plagdef.model.extension.cos_sim') as cos_sim:
        cluster_bow.return_value = {}
        # First clustering too broad, second results in two clusters which are both similar enough
        cos_sim.side_effect = [0, 1, 1]
        filtered_detections = extender._filter(set(clusters), 4)
    assert filtered_detections == {Detection(Cluster(frozenset({_create_seed(0, 5), _create_seed(1, 7)})), 1),
                                   Detection(Cluster(frozenset({_create_seed(6, 11)})), 1)}


def _create_sent(doc_name: str, sent_idx: int):
    doc1 = Document(doc_name, '')
    return FakeSentence(doc1, sent_idx, -1, -1, Counter(), {})


def _create_seed(sent1_idx: int, sent2_idx: int, doc1_name='doc1', doc2_name='doc2'):
    sent1 = _create_sent(doc1_name, sent1_idx)
    sent2 = _create_sent(doc2_name, sent2_idx)
    return Seed(sent1, sent2, 1, 1)
