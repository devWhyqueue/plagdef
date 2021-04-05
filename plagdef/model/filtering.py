from __future__ import annotations

from networkx import Graph, intersection, articulation_points, is_biconnected, is_empty

from plagdef.model.models import Cluster, RatedCluster


class ClusterFilter:
    def __init__(self, min_cluster_char_len: int):
        self._min_cluster_char_len = min_cluster_char_len

    def filtering(self, leg_obj, plags, psr):
        clusters = self.filter(leg_obj.clusters)
        leg_plags = [[(cluster.sents_doc1[0].idx, cluster.sents_doc1[-1].idx),
                      (cluster.sents_doc2[0].idx, cluster.sents_doc2[-1].idx)] for cluster in clusters]
        return leg_plags

    def filter(self, clusters: list[Cluster]):
        resolved_clusters = self._resolve_overlaps(set(clusters))
        return self._filter_small_clusters(resolved_clusters)

    def _resolve_overlaps(self, clusters: set[Cluster]) -> set[Cluster]:
        cluster_ols_doc1 = self._build_overlap_graph(clusters, in_first_doc=True)
        cluster_ols_doc2 = self._build_overlap_graph(clusters, in_first_doc=False)
        common_cluster_ols = self._intersect(cluster_ols_doc1, cluster_ols_doc2)
        cluster = self._next_cluster(common_cluster_ols)
        while cluster:
            ol_clusters = common_cluster_ols.adj[cluster]
            best_rated_cluster = RatedCluster(cluster, 0, 0)
            for ol_cluster in ol_clusters:
                better_rated_cluster = cluster.best_in_respect_to(ol_cluster)
                if better_rated_cluster > best_rated_cluster:
                    best_rated_cluster = better_rated_cluster
            if cluster == best_rated_cluster:
                common_cluster_ols.remove_nodes_from(ol_clusters)
            else:
                common_cluster_ols.remove_node(cluster)
            cluster = self._next_cluster(common_cluster_ols)
        return set(common_cluster_ols)

    def _build_overlap_graph(self, clusters: set[Cluster], in_first_doc: bool) -> Graph:
        graph = Graph()
        for cluster in clusters:
            graph.add_node(cluster)
            for ol_cluster in clusters:
                if cluster != ol_cluster and cluster.overlaps_with(ol_cluster, in_first_doc):
                    graph.add_edge(cluster, ol_cluster)
        return graph

    def _intersect(self, graph1: Graph, graph2: Graph):
        graph1.remove_nodes_from(list(n for n in graph1 if n not in graph2))
        graph2.remove_nodes_from(list(n for n in graph2 if n not in graph1))
        return intersection(graph1, graph2)

    def _next_cluster(self, graph: Graph):
        cluster = None
        if not is_empty(graph):
            if not is_biconnected(graph):
                cluster = next(articulation_points(graph))
            else:
                cluster = max(graph.degree, key=lambda x: x[1])[0]
        return cluster

    def _filter_small_clusters(self, clusters: set[Cluster]) -> set[Cluster]:
        filtered_clusters = set()
        for cluster in clusters:
            cluster_char_len_doc1 = cluster_char_len_doc2 = 0
            for sent in cluster.sents_doc1:
                cluster_char_len_doc1 += sent.length
            for sent in cluster.sents_doc2:
                cluster_char_len_doc2 += sent.length
            if cluster_char_len_doc1 >= self._min_cluster_char_len \
                and cluster_char_len_doc2 >= self._min_cluster_char_len:
                filtered_clusters.add(cluster)
        return filtered_clusters
