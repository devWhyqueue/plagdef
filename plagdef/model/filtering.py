from collections import defaultdict

from plagdef.model.models import Cluster, RatedCluster


class ClusterFilter:
    def filter(self, clusters: list[Cluster]):
        resolved_clusters = self._resolve_overlaps(set(clusters))

    def _resolve_overlaps(self, clusters: set[Cluster]) -> set[Cluster]:
        cluster_ols_doc1 = self._find_overlaps(clusters, in_first_doc=True)
        cluster_ols_doc2 = self._find_overlaps(clusters, in_first_doc=False)
        common_cluster_ols = self._intersect_overlaps(cluster_ols_doc1, cluster_ols_doc2)
        clusters = set()
        while len(common_cluster_ols):
            cluster, ol_clusters = common_cluster_ols.popitem()
            best_rated_cluster = RatedCluster(cluster, 0, 0)
            for ol_cluster in ol_clusters:
                better_rated_cluster = cluster.best_in_respect_to(ol_cluster)
                if better_rated_cluster > best_rated_cluster:
                    best_rated_cluster = better_rated_cluster
                if best_rated_cluster.cluster != ol_cluster:
                    del common_cluster_ols[ol_cluster]
            clusters.add(best_rated_cluster.cluster)
        return clusters

    def _find_overlaps(self, clusters: set[Cluster], in_first_doc: bool) -> dict[Cluster, set[Cluster]]:
        cluster_overlaps = defaultdict(lambda: set())
        for cluster in clusters:
            for ol_cluster in clusters:
                if cluster != ol_cluster and cluster.overlaps_with(ol_cluster, in_first_doc):
                    cluster_overlaps[cluster] |= ol_cluster
        return cluster_overlaps

    def _intersect_overlaps(self, cluster_overlaps_doc1: dict[Cluster, set[Cluster]],
                            cluster_overlaps_doc2: dict[Cluster, set[Cluster]]) \
        -> dict[Cluster, set[Cluster]]:
        common_det_overlaps = {}
        for cluster, ol_clusters_doc1, ol_clusters_doc2 \
            in zip(cluster_overlaps_doc1.keys(), cluster_overlaps_doc1.values(), cluster_overlaps_doc2.values()):
            common_overlap = ol_clusters_doc1.intersection(ol_clusters_doc2)
            if len(common_overlap):
                common_det_overlaps[cluster] = common_overlap
        return common_det_overlaps
