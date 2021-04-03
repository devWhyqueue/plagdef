from collections import Counter
from unittest.mock import patch

from plagdef.model.models import Document, Sentence, Cluster
from plagdef.tests.model.test_extension import _create_seeds


def test_documents_are_equal():
    doc1 = Document('doc', 'Arbitrary text.')
    doc2 = Document('doc', 'Some text.')
    assert doc1 == doc2


def test_documents_are_the_same_if_same_name():
    docs = set()
    docs.add(Document('doc', 'abc'))
    docs.add(Document('doc', 'cde'))
    assert len(docs) == 1


def test_document_sents_are_ordered_by_start_char():
    doc = Document('doc', '')
    doc.sents.add(Sentence(doc, 5, -1, Counter(), {}))
    doc.sents.add(Sentence(doc, 3, -1, Counter(), {}))
    doc.sents.add(Sentence(doc, 7, -1, Counter(), {}))
    assert [sent.start_char for sent in doc.sents] == [3, 5, 7]


def test_sentence_idx():
    doc = Document('doc', '')
    sent = Sentence(doc, 3, -1, Counter(), {})
    doc.sents.add(Sentence(doc, 4, -1, Counter(), {}))
    doc.sents.add(sent)
    doc.sents.add(Sentence(doc, 0, -1, Counter(), {}))
    assert sent.idx == 1


def test_sentences_are_equal_if_doc_and_start_char_are_equal():
    doc = Document('doc', '')
    sent1 = Sentence(doc, 3, 17, Counter(), {})
    sent2 = Sentence(doc, 3, 21, Counter({'xyz': 2}), {'xyz': 0.9845})  # unrealistic
    sent3 = Sentence(doc, 4, 17, Counter(), {})
    assert sent1 == sent2, sent1 != sent3


def test_sentences_are_the_same_if_doc_and_start_char_are_equal():
    doc = Document('doc', '')
    sents = set()
    sents.add(Sentence(doc, 3, 17, Counter(), {}))
    sents.add(Sentence(doc, 3, 21, Counter({'xyz': 2}), {'xyz': 0.9845}))  # unrealistic
    assert len(sents) == 1


def test_sentence_adjacent_to():
    sent1 = _create_sent('doc1', 0)
    sent2 = _create_sent('doc2', 5)
    adj = sent1.adjacent_to(sent2, 4)
    assert adj


def test_sentence_adjacent_to_with_gap_over_th():
    sent1 = _create_sent('doc1', 0)
    sent2 = _create_sent('doc2', 6)
    # Five sentences in-between
    adj = sent1.adjacent_to(sent2, 4)
    assert not adj


def test_clusters_are_equal_if_same_seeds():
    cluster1 = Cluster(_create_seeds([(0, 1), (10, 9)]))
    cluster2 = Cluster(_create_seeds([(10, 9), (0, 1)]))
    assert cluster1 == cluster2


def test_clusters_are_the_same_if_same_seeds():
    clusters = set()
    clusters.add(Cluster(_create_seeds([(0, 1), (10, 9)])))
    clusters.add(Cluster(_create_seeds([(10, 9), (0, 1)])))
    assert len(clusters) == 1


def test_cluster_contains_sents_from_both_docs():
    cluster = Cluster(_create_seeds([(3, 1), (10, 9)]))
    assert len(cluster.sents_doc1) == 8
    assert len(cluster.sents_doc2) == 9


def test_cluster_tf_isf_bow():
    # doc1: 'This is an awesome document. All of these bows are combined. Even this last one.'
    # doc2: 'This is another document. Just for good measure. As always.'
    # Just for this example. In reality the last two sentences are too different.
    cluster = Cluster(_create_seeds([(0, 0), (1, 1), (2, 2)]))
    # Simulate the preprocessing for doc1
    cluster.sents_doc1 = (Sentence(cluster._doc1, 0, -1, Counter(),
                                   {'this': 0.22, 'be': 0.51, 'a': 1.60, 'awesome': 1.60, 'document': 0.91}),
                          Sentence(cluster._doc1, 1, -1, Counter(),
                                   {'all': 1.60, 'of': 1.60, 'this': 0.22, 'bow': 1.60, 'be': 0.51, 'combine': 1.60}),
                          Sentence(cluster._doc1, 2, -1, Counter(),
                                   {'even': 1.60, 'this': 0.22, 'last': 1.60, 'one': 1.60}))
    tf_isf_bow_doc1 = cluster._tf_isf_bow(doc1_sents=True)
    assert tf_isf_bow_doc1 == {'this': 0.66, 'be': 1.02, 'a': 1.6, 'awesome': 1.6, 'document': 0.91,
                               'all': 1.6, 'of': 1.6, 'bow': 1.6, 'combine': 1.6, 'even': 1.6, 'last': 1.6, 'one': 1.6}


def test_clusters_overlap_if_they_share_a_sentence_in_first_doc():
    cluster1 = Cluster(_create_seeds([(0, 1), (4, 5)]))
    cluster2 = Cluster(_create_seeds([(3, 6), (7, 7)]))
    assert cluster1.overlaps_with(cluster2, in_first_doc=True)
    assert cluster2.overlaps_with(cluster1, in_first_doc=True)
    assert not cluster1.overlaps_with(cluster2, in_first_doc=False)
    assert not cluster2.overlaps_with(cluster1, in_first_doc=False)


def test_clusters_overlap_if_they_share_a_sentence_in_second_doc():
    cluster1 = Cluster(_create_seeds([(0, 1), (4, 5)]))
    cluster2 = Cluster(_create_seeds([(6, 5), (7, 7)]))
    assert cluster1.overlaps_with(cluster2, in_first_doc=False)
    assert not cluster1.overlaps_with(cluster2, in_first_doc=True)


def test_cluster_fragment_similarity():
    # Given an adjacent_sents_gap = 1, these overlapping clusters may exist
    cluster_a = Cluster(_create_seeds([(0, 4), (3, 2), (6, 0)]))
    cluster_b = Cluster(_create_seeds([(4, 8), (7, 5), (10, 2)]))
    # Calculating sim_{a.sents_doc2}(a.sents_doc1 ∩ b.sents_doc1)
    # fragment_sents: 4, 5, 6 (a.sents_doc1 ∩ b.sents_doc1)
    # cluster_sents: 0, 1, 2, 3, 4 (a.sents_doc2)
    # cos_sims for fragment_sent[0] for each cluster_sent: [0, 0, 0, 0.4, 0]
    # cos_sims for fragment_sent[1] for each cluster_sent: [0.6, 0, 0, 0, 0]
    # cos_sims for fragment_sent[2] for each cluster_sent: [0, 0, 0, 0, 0.5]
    with patch('plagdef.model.models.util.cos_sim') as cos_sim:
        cos_sim.side_effect = [0, 0, 0, 0.4, 0, 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0.5]
        sim = cluster_a._fragment_similarity(cluster_a.sents_doc1[4:7], cluster_a.sents_doc2)
    assert sim == 0.5


def test_cluster_rate_in_respect_to():
    # Given an adjacent_sents_gap = 1, these overlapping clusters may exist
    cluster_a = Cluster(_create_seeds([(0, 4), (3, 2), (6, 0)]))
    cluster_b = Cluster(_create_seeds([(4, 8), (7, 5), (10, 2)]))
    # Calculating q_{b}(a)
    # Then sim_{a.sents_doc2}(a.sents_doc1 ∩ b.sents_doc1) = 0.5
    # fragment_sents: 4, 5, 6 (a.sents_doc1 ∩ b.sents_doc1)
    # cluster_sents: 0, 1, 2, 3, 4 (a.sents_doc2)
    # cos_sims for fragment_sent[0] for each cluster_sent: [0, 0, 0, 0.4, 0]
    # cos_sims for fragment_sent[1] for each cluster_sent: [0.6, 0, 0, 0, 0]
    # cos_sims for fragment_sent[2] for each cluster_sent: [0, 0, 0, 0, 0.5]
    # and sim_{a.sents_doc2}(a.sents_doc1 / (a.sents_doc1 ∩ b.sents_doc1)) = 0.4
    # fragment_sents: 0, 1, 2, 3 (a.sents_doc1 / (a.sents_doc1 ∩ b.sents_doc1))
    # cluster_sents: 0, 1, 2, 3, 4 (a.sents_doc2)
    # cos_sims for fragment_sent[0] for each cluster_sent: [0, 0, 0, 0.4, 0]
    # cos_sims for fragment_sent[1] for each cluster_sent: [0.2, 0, 0, 0, 0]
    # cos_sims for fragment_sent[2] for each cluster_sent: [0, 0, 0, 0, 0.1]
    # cos_sims for fragment_sent[3] for each cluster_sent: [0, 0.9, 0, 0, 0]
    # => q_{b}(a) = 0.5 + (1 - 0.5) * 0.4 = 0.7, size: 7
    with patch('plagdef.model.models.util.cos_sim') as cos_sim:
        cos_sim.side_effect = [0, 0, 0, 0.4, 0, 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0.5,
                               0, 0, 0, 0.4, 0, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0, 0.9, 0, 0, 0]
        rated_cluster = cluster_a._rate_in_respect_to(cluster_b, first_doc_susp=True)
    assert rated_cluster.quality == 0.7
    assert rated_cluster.size == 7


def test_cluster_best_variant():
    # Given an adjacent_sents_gap = 1, these overlapping clusters may exist
    cluster_a = Cluster(_create_seeds([(0, 4), (3, 2), (6, 0)]))
    cluster_b = Cluster(_create_seeds([(4, 8), (7, 5), (10, 2)]))
    # Picking a variant a (doc1 is susp and doc2 is src) or b (doc2 is susp and doc1 is src)
    # a: q_{b}(a) = 0.5 + (1 - 0.5) * 0.4 = 0.7, size: 7
    # (for more details take a look at test_cluster_rate_in_respect_to())
    # b:
    # Calculating q_{b}(a)
    # Then sim_{a.sents_doc1}(a.sents_doc2 ∩ b.sents_doc2) = 0.6
    # fragment_sents: 2, 3, 4 (a.sents_doc2 ∩ b.sents_doc2)
    # cluster_sents: 0, 1, 2, 3, 4, 5, 6 (a.sents_doc1)
    # cos_sims for fragment_sent[0] for each cluster_sent: [0.5, 0, 0, 0.4, 0, 0, 0]
    # cos_sims for fragment_sent[1] for each cluster_sent: [0.6, 0.8, 0, 0, 0, 0, 0]
    # cos_sims for fragment_sent[2] for each cluster_sent: [0, 0, 0, 0, 0.5, 0, 0]
    # and sim_{a.sents_doc1}(a.sents_doc2 / (a.sents_doc2 ∩ b.sents_doc2)) = 0.3
    # fragment_sents: 0, 1 (a.sents_doc2 / (a.sents_doc2 ∩ b.sents_doc2))
    # cluster_sents: 0, 1, 2, 3, 4, 5, 6 (a.sents_doc1)
    # cos_sims for fragment_sent[0] for each cluster_sent: [0, 0, 0, 0.4, 0, 0, 0]
    # cos_sims for fragment_sent[1] for each cluster_sent: [0.2, 0, 0, 0, 0, 0, 0]
    # => q_{b}(a) = 0.6 + (1 - 0.6) * 0.3 = 0.72, size: 5
    with patch('plagdef.model.models.util.cos_sim') as cos_sim:
        cos_sim.side_effect = [0, 0, 0, 0.4, 0, 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0.5,
                               0, 0, 0, 0.4, 0, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0, 0.9, 0, 0, 0,
                               0.5, 0, 0, 0.4, 0, 0, 0, 0.6, 0.8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0,
                               0, 0, 0, 0.4, 0, 0, 0, 0.2, 0, 0, 0, 0, 0, 0]
        rated_cluster = cluster_a._best_variant(cluster_b)
    assert rated_cluster.quality == 0.72
    assert rated_cluster.size == 5


def test_cluster_best_in_respect_to():
    # Given an adjacent_sents_gap = 1, these overlapping clusters may exist
    cluster_a = Cluster(_create_seeds([(0, 4), (3, 2), (6, 0)]))
    cluster_b = Cluster(_create_seeds([(4, 8), (7, 5), (10, 2)]))
    # Best variant of cluster a: q_{b}(a) = 0.72, size: 5
    # Best variant of cluster b: q_{a}(b) = 0.74, size: 7
    with patch('plagdef.model.models.util.cos_sim') as cos_sim:
        cos_sim.side_effect = [0, 0, 0, 0.4, 0, 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0.5,
                               0, 0, 0, 0.4, 0, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0, 0.9, 0, 0, 0,
                               0.5, 0, 0, 0.4, 0, 0, 0, 0.6, 0.8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0,
                               0, 0, 0, 0.4, 0, 0, 0, 0.2, 0, 0, 0, 0, 0, 0,

                               0, 0, 0, 0.4, 0, 0, 0, 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5,
                               0, 0, 0, 0.4, 0, 0, 0, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0, 0.9, 0, 0, 0, 0,
                               0,
                               0.5, 0, 0, 0.4, 0, 0, 0, 0.6, 0.8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0,
                               0, 0, 0, 0.4, 0, 0, 0, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.4, 0, 0, 0, 0, 0, 0, 0.4, 0, 0,
                               0]
        rated_cluster = cluster_a.best_in_respect_to(cluster_b)
    assert rated_cluster.quality == 0.74
    assert rated_cluster.size == 7


def _create_sent(doc_name: str, sent_idx: int):
    doc = Document(doc_name, '')
    [doc.sents.add(Sentence(doc, idx, -1, Counter(), {})) for idx in range(sent_idx + 1)]
    return doc.sents[sent_idx]
