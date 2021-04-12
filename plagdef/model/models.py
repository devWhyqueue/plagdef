from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from functools import total_ordering

from sortedcontainers import SortedSet, SortedList

from plagdef.model import util


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


class Fragment:
    def __init__(self, start_char: int, end_char: int, doc: Document):
        self.start_char = start_char
        self.end_char = end_char
        self.doc = doc
        self.text = doc.text[start_char:end_char]

    def overlaps_with(self, other: Fragment) -> bool:
        if self.doc == other.doc:
            own_interval = set(range(self.start_char, self.end_char))
            other_interval = set(range(other.start_char, other.end_char))
            return len(own_interval.intersection(other_interval)) > 0
        return False

    def __eq__(self, other):
        if type(other) is type(self):
            return self.start_char == other.start_char and self.end_char == other.end_char and self.doc == other.doc
        return False

    def __hash__(self):
        return hash((self.start_char, self.doc))

    def __len__(self):
        return self.end_char - self.start_char


class Sentence(Fragment):
    def __init__(self, start_char: int, end_char: int, bow: Counter, doc: Document):
        super().__init__(start_char, end_char, doc)
        self.words = SortedList(key=lambda word: word.start_char)
        self.bow = bow
        self.tf_isf_bow = {}

    @property
    def idx(self):
        return self.doc.sents.index(self)

    def adjacent_to(self, other: Sentence, adjacent_sents_gap: int) -> bool:
        return abs(self.idx - other.idx) - 1 <= adjacent_sents_gap


class Word(Fragment):
    def __init__(self, start_char: int, end_char: int, sent: Sentence):
        super().__init__(start_char, end_char, sent.doc)
        self.sent = sent


@dataclass(frozen=True)
class Seed:
    sent1: Sentence
    sent2: Sentence
    cos_sim: float
    dice_sim: float

    def __repr__(self):
        return f'Seed({self.sent1.idx}, {self.sent2.idx}, {self.cos_sim}, {self.dice_sim})'


class Cluster:
    def __init__(self, seeds: set[Seed]):
        self.seeds = frozenset(seeds)
        self.doc1 = next(iter(self.seeds)).sent1.doc
        self.doc2 = next(iter(self.seeds)).sent2.doc
        self.sents_doc1 = tuple(self._sents(in_first_doc=True))
        self.sents_doc2 = tuple(self._sents(in_first_doc=False))
        self.tf_isf_bow_doc1 = self._tf_isf_bow(doc1_sents=True)
        self.tf_isf_bow_doc2 = self._tf_isf_bow(doc1_sents=False)
        self.cos_sim = util.cos_sim(self.tf_isf_bow_doc1, self.tf_isf_bow_doc2)

    def _sents(self, in_first_doc: bool) -> list[Sentence]:
        sent_idc = [seed.sent1.idx for seed in self.seeds] if in_first_doc else [seed.sent2.idx for seed in self.seeds]
        start = min(sent_idc)
        end = max(sent_idc)
        return self.doc1.sents[start:end + 1] if in_first_doc else self.doc2.sents[start:end + 1]

    def _tf_isf_bow(self, doc1_sents: bool) -> dict:
        sents = self.sents_doc1 if doc1_sents else self.sents_doc2
        sent_vec_sum = defaultdict(lambda: 0.0)
        for sent in sents:
            for lemma, tf_isf_val in sent.tf_isf_bow.items():
                sent_vec_sum[lemma] += tf_isf_val
        return sent_vec_sum

    def overlaps_with(self, other: Cluster) -> bool:
        """Contrary to Sanchez-Perez et al.'s algorithm,
        two clusters are considered overlapping if and only if
        they share at least one sentence in doc1 and doc2."""
        return any([sent in other.sents_doc1 for sent in self.sents_doc1]) \
               and any([sent in other.sents_doc2 for sent in self.sents_doc2])

    def best_with_respect_to(self, ol_cluster: Cluster) -> RatedCluster:
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
        a = self._rate_with_respect_to(ol_cluster, first_doc_susp=True)
        b = self._rate_with_respect_to(ol_cluster, first_doc_susp=False)
        return a if a >= b else b

    def _rate_with_respect_to(self, ol_cluster: Cluster, first_doc_susp: bool) -> RatedCluster:
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

    def char_lengths(self) -> tuple[int, int]:
        char_len_doc1 = sum([len(sent) for sent in self.sents_doc1])
        char_len_doc2 = sum([len(sent) for sent in self.sents_doc2])
        return char_len_doc1, char_len_doc2

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
        self.size = size  # number of sentences

    def __lt__(self, other: RatedCluster) -> bool:
        if (self.quality > 0.99 and other.quality > 0.99) or self.quality == other.quality:
            return self.size < other.size
        else:
            return self.quality < other.quality

    def __eq__(self, other):
        if type(other) is type(self):
            return self.quality == other.quality and self.size == other.size and self.cluster == other.cluster
        return False


class Match:
    def __init__(self, frag1: Fragment, frag2: Fragment):
        if frag1.doc == frag2.doc:
            raise SameDocumentError('Each fragment must belong to its own distinct document.')
        self.frag_pair = frozenset({frag1, frag2})

    @classmethod
    def from_cluster(cls, cluster: Cluster) -> Match:
        text_doc1_start, text_doc1_end = cluster.sents_doc1[0].start_char, cluster.sents_doc1[-1].end_char
        text_doc2_start, text_doc2_end = cluster.sents_doc2[0].start_char, cluster.sents_doc2[-1].end_char
        return Match(Fragment(text_doc1_start, text_doc1_end, cluster.doc1),
                     Fragment(text_doc2_start, text_doc2_end, cluster.doc2))

    def overlaps_with(self, other: Match) -> bool:
        frag1, frag2 = self.frag_pair
        return any([frag1.overlaps_with(other_frag) for other_frag in other.frag_pair]) \
               and any([frag2.overlaps_with(other_frag) for other_frag in other.frag_pair])

    def frag_from_doc(self, doc: Document):
        return next(filter(lambda frag: frag.doc == doc, self.frag_pair), None)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.frag_pair == other.frag_pair
        return False

    def __hash__(self):
        return hash(self.frag_pair)

    def __len__(self):
        return sum([len(frag) for frag in self.frag_pair])


class DocumentPairMatches:
    def __init__(self, matches=None):
        self.doc_pair = set()
        self._matches = set()
        if matches:
            [self.add(match) for match in matches]

    def add(self, match: Match):
        frag1, frag2 = match.frag_pair
        if len(self):
            if not self.doc_pair == {frag1.doc, frag2.doc}:
                raise DifferentDocumentPairError(f'Only matches of document pair {self.doc_pair} can be added.')
        else:
            self.doc_pair.update({frag1.doc, frag2.doc})
        self._matches.add(match)

    def list(self) -> set[Match]:
        return self._matches

    def __len__(self):
        return len(self._matches)


class DifferentDocumentPairError(Exception):
    pass


class SameDocumentError(Exception):
    pass
