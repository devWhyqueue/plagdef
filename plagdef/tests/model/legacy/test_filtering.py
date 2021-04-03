from plagdef.model.legacy.filtering import LegacyClusterFilter
from plagdef.tests.model.legacy.test_extension import _create_seed


def test_remove_overlap_with_non_overlapping_detections():
    clusters = [[_create_seed(0, 5), _create_seed(1, 7)], [_create_seed(6, 11)]]
    plags = [[(0, 1), (5, 7)], [(6, 6), (11, 11)]]
    cluster_filter = LegacyClusterFilter()
    filtered_plags, filtered_clusters = cluster_filter.remove_overlap3(plags, clusters, [], [])
    assert (clusters, plags) == (filtered_clusters, filtered_plags)

# Given the low testability of the code and the change of the notion of an overlap, it would not be of any use to
# extensively test the legacy code. However, the new code is tested against the formal definitions of quality and
# fragment similarity.
