from plagdef.model.legacy.algorithm import SGSPLAG
from plagdef.model.legacy.seeding import LegacySentenceMatcher


def test_seeding_returns_seeds(config):
    doc1_sent_bows = doc2_sent_bows = [{'this': 1.0986, 'be': 0.0, 'a': 1.0986, 'document': 1.0986},
                                       {'all': 1.0986, 'the': 2.1972, 'word': 1.0986, 'be': 0.0, 'same': 1.0986},
                                       {'even': 1.0986, 'these': 1.0986, 'last': 1.0986, 'one': 1.0986, 'be': 0.0}]
    obj = SGSPLAG('This is a document. All the words are the same. Even these last ones are.',
                  'This is a document. All the words are the same. Even these last ones are.', config)
    obj.susp_bow, obj.src_bow = doc1_sent_bows, doc2_sent_bows
    sent_matcher = LegacySentenceMatcher()
    seeds = sent_matcher.seeding(obj)
    assert len(seeds) == len(doc1_sent_bows)
    assert [s[:2] for s in seeds] == [(0, 0), (1, 1), (2, 2)]

