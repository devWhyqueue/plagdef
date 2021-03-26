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


def _create_seed(sent1_idx: int, sent2_idx: int):
    return sent1_idx, sent2_idx, 1, 1
