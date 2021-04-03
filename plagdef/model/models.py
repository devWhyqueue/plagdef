from __future__ import annotations

from collections import Counter, Iterable, defaultdict
from dataclasses import dataclass
from functools import total_ordering

from sortedcontainers import SortedSet

from plagdef.model import util


@dataclass
class Document:
    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text
        self.vocab = Counter()  # <lemma, sent_freq>
        self.sents = SortedSet(key=lambda sent: sent.start_char)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"Document('{self.name}')"


@dataclass
class Sentence:
    doc: Document
    start_char: int
    end_char: int
    bow: Counter
    tf_isf_bow: dict

    @property
    def idx(self):
        return self.doc.sents.index(self)

    def adjacent_to(self, other: Sentence, adjacent_sents_gap: int) -> bool:
        return abs(self.idx - other.idx) - 1 <= adjacent_sents_gap

    def __eq__(self, other):
        if type(other) is type(self):
            return self.doc == other.doc and self.start_char == other.start_char
        return False

    def __hash__(self):
        return hash((self.doc, self.start_char))


@dataclass(frozen=True)
class Seed:
    sent1: Sentence
    sent2: Sentence
    cos_sim: float
    dice_sim: float

    def __repr__(self):
        return f'Seed({self.sent1.idx}, {self.sent2.idx}, {self.cos_sim}, {self.dice_sim})'


@dataclass
class Cluster:
    def __init__(self, seeds: set[Seed]):
        self.seeds = frozenset(seeds)
        self._doc1 = next(iter(self.seeds)).sent1.doc
        self._doc2 = next(iter(self.seeds)).sent2.doc
        self.sents_doc1 = tuple(self._sents(in_first_doc=True))
        self.sents_doc2 = tuple(self._sents(in_first_doc=False))
        self.tf_isf_bow_doc1 = self._tf_isf_bow(doc1_sents=True)
        self.tf_isf_bow_doc2 = self._tf_isf_bow(doc1_sents=False)
        self.cos_sim = util.cos_sim(self.tf_isf_bow_doc1, self.tf_isf_bow_doc2)

    def _sents(self, in_first_doc: bool) -> list[Sentence]:
        sent_idc = [seed.sent1.idx for seed in self.seeds] if in_first_doc else [seed.sent2.idx for seed in self.seeds]
        start = min(sent_idc)
        end = max(sent_idc)
        return self._doc1.sents[start:end + 1] if in_first_doc else self._doc2.sents[start:end + 1]

    def _tf_isf_bow(self, doc1_sents: bool) -> dict:
        sents = self.sents_doc1 if doc1_sents else self.sents_doc2
        sent_vec_sum = defaultdict(lambda: 0.0)
        for sent in sents:
            for lemma, tf_isf_val in sent.tf_isf_bow.items():
                sent_vec_sum[lemma] += tf_isf_val
        return sent_vec_sum

    def overlaps_with(self, other: Cluster, in_first_doc: bool) -> bool:
        own_sents = self.sents_doc1 if in_first_doc else self.sents_doc2
        other_sents = other.sents_doc1 if in_first_doc else other.sents_doc2
        return any([sent in other_sents for sent in own_sents])

    def best_in_respect_to(self, ol_cluster: Cluster) -> RatedCluster:
        """Pick the best of the two overlapping clusters depending on their quality and size."""
        own = self._best_variant(ol_cluster)
        ol_cluster = ol_cluster._best_variant(self)
        return own if own >= ol_cluster else ol_cluster

    def _best_variant(self, ol_cluster: Cluster) -> RatedCluster:
        """Pick the best variant of the two possible qualities of a cluster.
        a: For each of the clusters' overlapping sentences in doc1 the algorithm looks for the most similar
        sentence in doc2 (from which doc1 potentially plagiarized this sentence). If this quality a computed with the
        clusters' overlapping fragments in doc1 combined with this cluster's non-overlapping fragment in doc1 is higher
        than or equal to b it is returned.
        b: For each of the clusters' overlapping sentences in doc2 the algorithm looks for the most similar
        sentence in doc1 (from which doc2 potentially plagiarized this sentence). If this quality b computed with the
        clusters' overlapping fragments in doc2 combined with this cluster's non-overlapping fragment in doc2 is higher
        than a it is returned."""
        a = self._rate_in_respect_to(ol_cluster, first_doc_susp=True)
        b = self._rate_in_respect_to(ol_cluster, first_doc_susp=False)
        return a if a >= b else b

    def _rate_in_respect_to(self, ol_cluster: Cluster, first_doc_susp: bool) -> RatedCluster:
        """Compute the quality of this cluster in respect to an overlapping cluster ol_cluster according to the
        formula:
        q_{ol_cluster}(self) = sim_{self.sents_doc2}(O) + (1 - sim_{self.sents_doc2}(O))
        + sim_{self.sents_doc2}(N), O = self.sents_doc1 ∩ ol_cluster.sents_doc1 being the overlap in doc1
        and N = self.sents_doc1 / O the non-overlapping fragment in this cluster. The parameter first_doc_susp exchanges
        doc1 and doc2 in the formula."""
        own_sents_susp = self.sents_doc1 if first_doc_susp else self.sents_doc2
        own_sents_src = self.sents_doc2 if first_doc_susp else self.sents_doc1
        other_sents_susp = ol_cluster.sents_doc1 if first_doc_susp else ol_cluster.sents_doc2
        ol_sents_susp = set(filter(lambda susp_sent: susp_sent in other_sents_susp, own_sents_susp))
        own_non_ol_sents_susp = set(own_sents_susp).difference(ol_sents_susp)
        ol_sim = self._fragment_similarity(ol_sents_susp, own_sents_src)
        non_ol_sim = self._fragment_similarity(own_non_ol_sents_susp, own_sents_src)
        return RatedCluster(self, ol_sim + (1 - ol_sim) * non_ol_sim, len(own_sents_susp))

    def _fragment_similarity(self, fragment_sents: Iterable[Sentence], cluster_sents: Iterable[Sentence]) -> float:
        """Compute the non-symmetric similarity of a cluster's fragment in document a (fragment_sents) to the whole
        cluster fragment in document b (cluster_sents) according to the formula:
        sim_{cluster_sents}(fragment_sents) = 1/|fragment_sents|
            * sum_{s in fragment_sents}(max_{r in cluster_sents}(cos(s,r)))
        """
        similarity = 0.0
        frag_sents_len = 0
        for frag_sent in fragment_sents:
            similarity += max([util.cos_sim(frag_sent.tf_isf_bow, cluster_sent.tf_isf_bow)
                               for cluster_sent in cluster_sents])
            frag_sents_len += 1
        return similarity / frag_sents_len if frag_sents_len else 0

    def __eq__(self, other):
        if type(other) is type(self):
            return self.seeds == other.seeds
        return False

    def __hash__(self):
        return hash(self.seeds)

    def __repr__(self):
        if not len(self.seeds):
            return 'Cluster()'
        string = 'Cluster('
        for seed in self.seeds:
            string = string + f'{repr(seed)}, '
        return f'{string[:-2]})'


@total_ordering
class RatedCluster:
    def __init__(self, cluster: Cluster, quality: float, size: int):
        self.cluster = cluster
        self.quality = quality
        self.size = size

    def __lt__(self, other: RatedCluster) -> bool:
        if (self.quality > 0.99 and other.quality > 0.99) or self.quality == other.quality:
            return self.size < other.size
        else:
            return self.quality < other.quality
