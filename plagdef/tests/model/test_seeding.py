from collections import Counter

from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.preprocessing import Sentence
from plagdef.model.seeding import Seed


def test_seeding_returns_seeds(seeder, config):
    doc1_sent_bows = doc2_sent_bows = [{'this': 1.0986, 'be': 0.0, 'a': 1.0986, 'document': 1.0986},
                                       {'all': 1.0986, 'the': 2.1972, 'word': 1.0986, 'be': 0.0, 'same': 1.0986},
                                       {'even': 1.0986, 'these': 1.0986, 'last': 1.0986, 'one': 1.0986, 'be': 0.0}]
    obj = SGSPLAG('This is a document. All the words are the same. Even these last ones are.',
                  'This is a document. All the words are the same. Even these last ones are.', config)
    obj.susp_bow, obj.src_bow = doc1_sent_bows, doc2_sent_bows
    seeds = seeder.seeding(obj)
    assert len(seeds) == len(doc1_sent_bows)
    assert [s[:2] for s in seeds] == [(0, 0), (1, 1), (2, 2)]


def test_match_returns_nothing_if_not_similar(seeder):
    sen1 = Sentence(None, -1, -1, Counter({'this': 1, 'be': 1, 'a': 1, 'document': 1}),
                    {'this': 0.69, 'be': 0.0, 'a': 0.69, 'document': 0.69})
    sen2 = Sentence(None, -1, -1, Counter({'these': 1, 'however': 1, 'be': 1, 'different': 1, 'word': 1}),
                    {'these': 0.69, 'be': 0.0, 'different': 0.69,
                     'word': 0.69, 'however': 0.69})
    match = seeder._match(sen1, sen2)
    assert not match


def test_match_returns_match_if_similar(seeder):
    # We need a second sentence with some different words because otherwise every term would have zero specificity
    # doc1/doc2: 'The words are all the same. Even these are.'
    doc1_sent1 = doc2_sent1 = Sentence(None, -1, -1, Counter({'the': 2, 'word': 1, 'be': 1, 'all': 1, 'same': 1}),
                                       {'the': 1.38, 'word': 0.69, 'be': 0.0, 'all': 0.69, 'same': 0.69})
    match = seeder._match(doc1_sent1, doc2_sent1)
    assert match == Seed(doc1_sent1, doc2_sent1, 1, 1)
