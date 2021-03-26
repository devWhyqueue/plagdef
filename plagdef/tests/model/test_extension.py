from collections import Counter
from itertools import combinations
from random import randint

from plagdef.model.extension import SeedExtender, Cluster
from plagdef.model.legacy.extension import LegacySeedExtender
from plagdef.model.preprocessing import Document, Sentence
from plagdef.model.seeding import Seed


def test_adjacent_sents():
    sent1 = _create_sent('doc1', 0)
    sent2 = _create_sent('doc2', 5)
    extender = SeedExtender(4, 1)
    adjacent = extender._adjacent(sent1, sent2)
    assert adjacent


def test_adjacent_sents_with_gap_over_th():
    sent1 = _create_sent('doc1', 0)
    sent2 = _create_sent('doc2', 6)
    extender = SeedExtender(4, 1)
    # Five sentences in-between
    adjacent = extender._adjacent(sent1, sent2)
    assert not adjacent


def test_clusters_are_equal():
    cluster1 = Cluster({_create_seed(0, 0), _create_seed(3, 1)})
    cluster2 = Cluster({_create_seed(3, 1), _create_seed(0, 0)})
    assert cluster1 == cluster2


def test_cluster_sets_are_equal():
    cluster1 = Cluster({_create_seed(0, 0), _create_seed(3, 1)})
    cluster2 = Cluster({_create_seed(3, 1), _create_seed(0, 0)})
    assert {cluster1, cluster2} == {cluster2, cluster1}


def test_clustering_with_equal_clusters():
    # The given seeds form these clusters:
    # doc1: [[s0, s1], [s2, s3]]
    # doc2: [[s0, s1], [s2, s3]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = [_create_seed(0, 0),
             _create_seed(3, 1),
             _create_seed(9, 7),
             _create_seed(10, 9)]
    extender = SeedExtender(4, 1)
    clusters = extender.extend(set(seeds))
    assert clusters == {Cluster({seeds[0], seeds[1]}), Cluster({seeds[2], seeds[3]})}


def test_clustering_with_more_clusters_in_doc1():
    # The given seeds form these clusters:
    # doc1: [[s0, s1], [s2]]
    # doc2: [[s0, s1, s2]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = [_create_seed(0, 0),
             _create_seed(3, 1),
             _create_seed(9, 6)]
    extender = SeedExtender(4, 1)
    clusters = extender.extend(set(seeds))
    assert clusters == {Cluster({seeds[0], seeds[1]}), Cluster({seeds[2]})}


def test_clustering_with_more_clusters_in_doc2():
    # The given seeds form these clusters:
    # doc1: [[s0, s1, s2]]
    # doc2: [[s0, s1], [s2]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = [_create_seed(0, 0),
             _create_seed(3, 1),
             _create_seed(7, 8)]
    extender = SeedExtender(4, 1)
    clusters = extender.extend(set(seeds))
    assert clusters == {Cluster({seeds[0], seeds[1]}), Cluster({seeds[2]})}


def test_clustering_with_totally_different_clusters():
    # The given seeds form these clusters:
    # doc1: [[s0, s1, s2, s3]]
    # doc2: [[s0], [s1], [s2], [s3]]
    # (doc1_sent_idx, doc2_sent_idx)
    seeds = [_create_seed(0, 0),
             _create_seed(3, 6),
             _create_seed(5, 12),
             _create_seed(7, 18)]
    extender = SeedExtender(4, 1)
    clusters = extender.extend(set(seeds))
    assert clusters == {Cluster({seeds[0]}), Cluster({seeds[1]}),
                        Cluster({seeds[2]}), Cluster({seeds[3]})}


def test_clustering_with_seed_which_is_part_of_different_clusters():
    # doc1: [[s0], [s1, s2], [s3], [s4]]
    # doc2: [[s0], [s1], [s2, s3], [s4]]
    seeds = [_create_seed(18, 17), _create_seed(36, 33), _create_seed(37, 49),
             _create_seed(54, 53), _create_seed(74, 63)]
    extender = SeedExtender(4, 1)
    clusters = extender.extend(set(seeds))
    assert clusters == {Cluster({seeds[0]}), Cluster({seeds[1]}), Cluster({seeds[2]}),
                        Cluster({seeds[3]}), Cluster({seeds[4]})}


def test_clustering_with_three_seeds_in_cluster():
    # doc1: [[s0], [s1, s2, s3], [s4]]
    # doc2: [[s0], [s1], [s2, s3], [s4]]
    seeds = [_create_seed(2, 17), _create_seed(21, 34), _create_seed(25, 43),
             _create_seed(30, 45), _create_seed(50, 51)]
    extender = SeedExtender(4, 1)
    clusters = extender.extend(set(seeds))
    assert clusters == {Cluster({seeds[0]}), Cluster({seeds[1]}),
                        Cluster({seeds[2], seeds[3]}), Cluster({seeds[4]})}


def test_clustering_processing_order_is_important():
    # doc1: [[s0, s1, s2], [s3, s4, s5]]
    # doc2: [[s0, s1], [s2, s3], [s4, s5]]
    seeds = [_create_seed(4, 0), _create_seed(7, 2),
             _create_seed(10, 12), _create_seed(19, 14),
             _create_seed(21, 23), _create_seed(26, 28)]
    extender = SeedExtender(4, 1)
    clusters = extender.extend(set(seeds))
    assert clusters == {Cluster({seeds[0], seeds[1]}),
                        Cluster({seeds[2]}), Cluster({seeds[3]}),
                        Cluster({seeds[4], seeds[5]})}


def test_clustering_seed_order_makes_no_difference():
    # doc1: [[s0, s1]]
    # doc2: [[s1, s0]]
    seeds = [_create_seed(0, 4), _create_seed(5, 1)]
    extender = SeedExtender(4, 1)
    clusters = extender.extend(set(seeds))
    assert clusters == {Cluster({seeds[0], seeds[1]})}


def test_compare_clustering_with_legacy():
    extender = SeedExtender(4, 1)
    legacy_extender = LegacySeedExtender()
    docs = [Document(f'doc{i}', '') for i in range(1, 11)]
    for doc1, doc2 in combinations(docs, 2):
        doc1_idx = doc2_idx = -1
        seeds = []
        for i in range(100):
            doc1_idx, doc2_idx = randint(doc1_idx + 1, doc1_idx + 20), randint(doc2_idx + 1, doc2_idx + 10)
            seeds.append(_create_seed(doc1_idx, doc2_idx, doc1.name, doc2.name))
        clusters = extender.extend(set(seeds))
        leg_clusters = legacy_extender._clustering(
            [(seed.sent1.idx, seed.sent2.idx, seed.cos_sim, seed.dice_sim) for seed in seeds],
            None, None, 4, 4, 1, 1, 0, 0)
        conv_leg_clusters = set()
        for cluster in leg_clusters:
            cluster_seeds = {_create_seed(seed[0], seed[1], doc1.name, doc2.name) for seed in cluster}
            conv_leg_clusters.add(Cluster(cluster_seeds))
        assert clusters == conv_leg_clusters


def _create_sent(doc_name: str, sent_idx: int):
    doc1 = Document(doc_name, '')
    return Sentence(doc1, sent_idx, -1, -1, Counter(), {})


def _create_seed(sent1_idx: int, sent2_idx: int, doc1_name='doc1', doc2_name='doc2'):
    sent1 = _create_sent(doc1_name, sent1_idx)
    sent2 = _create_sent(doc2_name, sent2_idx)
    return Seed(sent1, sent2, 1, 1)
