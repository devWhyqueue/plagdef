from unittest.mock import patch

from plagdef.model.legacy.extension import LegacySeedExtender


def test_adjacent_sents():
    extender = LegacySeedExtender()
    adjacent = extender._adjacent_sents(0, 5, 4)
    assert adjacent


def test_adjacent_sents_with_gap_over_th():
    extender = LegacySeedExtender()
    # Five sentences in-between
    adjacent = extender._adjacent_sents(0, 6, 4)
    assert not adjacent


def test_clustering_with_equal_clusters():
    # The given seeds form these clusters:
    # doc1: [[s0, s1], [s2, s3]]
    # doc2: [[s0, s1], [s2, s3]]
    # (doc1_sent_idx, doc2_sent_idx, cos_sim, dice_sim)
    seeds = [(0, 0, 1, 1),
             (3, 1, 1, 1),
             (9, 7, 1, 1),
             (10, 9, 1, 1)]
    extender = LegacySeedExtender()
    clusters = extender._clustering(seeds, None, None, 4, 4, 1, 1, 0, 0)
    assert clusters == [[(0, 0, 1, 1), (3, 1, 1, 1)],
                        [(9, 7, 1, 1), (10, 9, 1, 1)]]


def test_clustering_with_more_clusters_in_doc1():
    # The given seeds form these clusters:
    # doc1: [[s0, s1], [s2]]
    # doc2: [[s0, s1, s2]]
    # (doc1_sent_idx, doc2_sent_idx, cos_sim, dice_sim)
    seeds = [(0, 0, 1, 1),
             (3, 1, 1, 1),
             (9, 6, 1, 1)]
    extender = LegacySeedExtender()
    clusters = extender._clustering(seeds, None, None, 4, 4, 1, 1, 0, 0)
    assert clusters == [[(0, 0, 1, 1), (3, 1, 1, 1)],
                        [(9, 6, 1, 1)]]


def test_clustering_with_more_clusters_in_doc2():
    # The given seeds form these clusters:
    # doc1: [[s0, s1, s2]]
    # doc2: [[s0, s1], [s2]]
    # (doc1_sent_idx, doc2_sent_idx, cos_sim, dice_sim)
    seeds = [(0, 0, 1, 1),
             (3, 1, 1, 1),
             (7, 8, 1, 1)]
    extender = LegacySeedExtender()
    clusters = extender._clustering(seeds, None, None, 4, 4, 1, 1, 0, 0)
    assert clusters == [[(0, 0, 1, 1), (3, 1, 1, 1)],
                        [(7, 8, 1, 1)]]


def test_clustering_with_totally_different_clusters():
    # The given seeds form these clusters:
    # doc1: [[s0, s1, s2, s3]]
    # doc2: [[s0], [s1], [s2], [s3]]
    # (doc1_sent_idx, doc2_sent_idx, cos_sim, dice_sim)
    seeds = [(0, 0, 1, 1),
             (3, 6, 1, 1),
             (5, 12, 1, 1),
             (7, 18, 1, 1)]
    extender = LegacySeedExtender()
    clusters = extender._clustering(seeds, None, None, 4, 4, 1, 1, 0, 0)
    assert clusters == [[(0, 0, 1, 1)], [(3, 6, 1, 1)],
                        [(5, 12, 1, 1)], [(7, 18, 1, 1)]]


def test_clustering_with_seed_which_is_part_of_different_clusters():
    # doc1: [[s0], [s1, s2], [s3], [s4]]
    # doc2: [[s0], [s1], [s2, s3], [s4]]
    seeds = [_create_seed(18, 17), _create_seed(36, 33), _create_seed(37, 49),
             _create_seed(54, 53), _create_seed(74, 63)]
    extender = LegacySeedExtender()
    clusters = extender._clustering(seeds, None, None, 4, 4, 1, 1, 0, 0)
    assert clusters == [[seeds[0]], [seeds[1]], [seeds[2]], [seeds[3]], [seeds[4]]]


def test_clustering_with_three_seeds_in_cluster():
    # doc1: [[s0], [s1, s2, s3], [s4]]
    # doc2: [[s0], [s1], [s2, s3], [s4]]
    seeds = [_create_seed(2, 17), _create_seed(21, 34), _create_seed(25, 43),
             _create_seed(30, 45), _create_seed(50, 51)]
    extender = LegacySeedExtender()
    clusters = extender._clustering(seeds, None, None, 4, 4, 1, 1, 0, 0)
    assert clusters == [[seeds[0]], [seeds[1]], [seeds[2], seeds[3]], [seeds[4]]]


def test_clustering_processing_order_is_important():
    # doc1: [[s0, s1, s2], [s3, s4, s5]]
    # doc2: [[s0, s1], [s2, s3], [s4, s5]]
    seeds = [_create_seed(4, 0), _create_seed(7, 2),
             _create_seed(10, 12), _create_seed(19, 14),
             _create_seed(21, 23), _create_seed(26, 28)]
    extender = LegacySeedExtender()
    clusters = extender._clustering(seeds, None, None, 4, 4, 1, 1, 0, 0)
    assert clusters == [[seeds[0], seeds[1]], [seeds[2]], [seeds[3]], [seeds[4], seeds[5]]]


def test_clustering_seed_order_makes_no_difference():
    # doc1: [[s0, s1]]
    # doc2: [[s1, s0]]
    seeds = [_create_seed(0, 4), _create_seed(5, 1)]
    extender = LegacySeedExtender()
    clusters = extender._clustering(seeds, None, None, 4, 4, 1, 1, 0, 0)
    assert clusters == [[seeds[1], seeds[0]]]


def test_validation_with_only_similar_clusters():
    clusters = [[_create_seed(0, 2), _create_seed(2, 4)],
                [_create_seed(10, 5), _create_seed(11, 7), _create_seed(14, 11)]]
    detections = [[(0, 2), (2, 4)], [(10, 14), (5, 11)]]
    extender = LegacySeedExtender()
    # Calculation of cluster similarity untested
    with patch('plagdef.model.legacy.extension.range') as rng, \
        patch('plagdef.model.legacy.extension.cosine_measure') as cos_measure:
        rng.return_value = []
        cos_measure.return_value = 1
        filtered_detections = extender._validation(detections, clusters, None, None, None, None, 4, 0, 4, 0, 0, 0, 0.34)
    assert filtered_detections[0] == detections
    assert filtered_detections[1] == clusters
    assert filtered_detections[2] == [1, 1]


def test_validation_with_cluster_with_similarity_below_th():
    clusters = [[_create_seed(0, 2)]]
    detections = [[(0, 0), (2, 2)]]
    extender = LegacySeedExtender()
    # Calculation of cluster similarity untested
    with patch('plagdef.model.legacy.extension.range') as rng, \
        patch('plagdef.model.legacy.extension.cosine_measure') as cos_measure:
        rng.return_value = []
        cos_measure.return_value = 0
        filtered_detections = extender._validation(detections, clusters, None, None, None, None, 4, 0, 4, 0, 0, 0, 0.34)
    assert filtered_detections[0] == filtered_detections[1] == filtered_detections[2] == []


def test_validation_with_cluster_which_is_reduced():
    clusters = [[_create_seed(0, 5), _create_seed(1, 7), _create_seed(6, 11)]]
    detections = [[(0, 6), (5, 11)]]
    extender = LegacySeedExtender()
    # Calculation of cluster similarity untested
    with patch('plagdef.model.legacy.extension.range') as rng, \
        patch('plagdef.model.legacy.extension.cosine_measure') as cos_measure:
        rng.return_value = []
        # First clustering too broad, second results in two clusters which are both similar enough
        cos_measure.side_effect = [0, 1, 1]
        filtered_detections = extender._validation(detections, clusters, None, None, None, None, 4, 0, 4, 0, 0, 0, 0.34)
    assert filtered_detections[0] == [[(0, 1), (5, 7)], [(6, 6), (11, 11)]]
    assert filtered_detections[1] == [[_create_seed(0, 5), _create_seed(1, 7)], [_create_seed(6, 11)]]
    assert filtered_detections[2] == [1, 1]


def _create_seed(sent1_idx: int, sent2_idx: int):
    return sent1_idx, sent2_idx, 1, 1
