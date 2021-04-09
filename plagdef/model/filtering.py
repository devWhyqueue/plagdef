from __future__ import annotations

from networkx import Graph, articulation_points, is_biconnected, is_empty

from plagdef.model.models import Cluster, RatedCluster


class ClusterFilter:
    def __init__(self, min_cluster_char_len: int):
        self._min_cluster_char_len = min_cluster_char_len

    def filter(self, clusters: set[Cluster]):
        resolved_clusters = _resolve_overlaps(clusters)
        return self._remove_small_clusters(resolved_clusters)

    def _remove_small_clusters(self, clusters: set[Cluster]) -> set[Cluster]:
        filtered_clusters = set()
        for cluster in clusters:
            cluster_char_lengths = cluster.char_lengths()
            if cluster_char_lengths[0] >= self._min_cluster_char_len \
                and cluster_char_lengths[1] >= self._min_cluster_char_len:
                filtered_clusters.add(cluster)
        return filtered_clusters


def _resolve_overlaps(clusters: set[Cluster]) -> set[Cluster]:
    overlap_graph = _build_overlap_graph(clusters)
    overlapping_cluster = _next_overlapping_cluster(overlap_graph)
    while overlapping_cluster:
        ol_clusters = overlap_graph.adj[overlapping_cluster]
        best_rated_cluster = RatedCluster(overlapping_cluster, 0, 0)
        for ol_cluster in ol_clusters:
            better_rated_cluster = overlapping_cluster.best_in_respect_to(ol_cluster)
            if better_rated_cluster > best_rated_cluster:
                best_rated_cluster = better_rated_cluster
        if overlapping_cluster == best_rated_cluster:
            overlap_graph.remove_nodes_from(ol_clusters)
        else:
            overlap_graph.remove_node(overlapping_cluster)
        overlapping_cluster = _next_overlapping_cluster(overlap_graph)
    return set(overlap_graph)


def _build_overlap_graph(clusters: set[Cluster]) -> Graph:
    graph = Graph()
    for cluster in clusters:
        graph.add_node(cluster)
        for ol_cluster in clusters:
            if cluster != ol_cluster and cluster.overlaps_with(ol_cluster):
                graph.add_edge(cluster, ol_cluster)
    return graph


def _next_overlapping_cluster(graph: Graph):
    cluster = None
    if not is_empty(graph):
        if not is_biconnected(graph):
            cluster = next(articulation_points(graph))
        else:
            cluster = max(graph.degree, key=lambda x: x[1])[0]
    return cluster
