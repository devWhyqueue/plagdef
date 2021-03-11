from pytest import fixture

from plagdef.model.legacy.algorithm import DocumentPairMatches, Match, Section
from plagdef.model.preprocessing import DocumentFactory


@fixture(scope='session')
def config():
    return {
        'th1': 0.3, 'th2': 0.33, 'th3': 0.34,
        'src_gap': 4, 'src_gap_least': 0, 'susp_gap': 4, 'susp_gap_least': 0,
        'verbatim_minlen': 256, 'src_size': 1, 'susp_size': 1, 'min_sent_len': 3, 'min_plaglen': 15,
        'rem_stop_words': False, 'verbatim': 1, 'summary': 1, 'src_gap_summary': 24, 'susp_gap_summary': 24
    }


@fixture(scope='session')
def doc_factory(config):
    return DocumentFactory('eng', config['min_sent_len'], config['rem_stop_words'])


@fixture
def real_docs(doc_factory):
    return doc_factory.create('doc1', 'Plagiarism is not the same as copyright infringement. While both terms may '
                                      'apply to a particular act, they are different concepts. Copyright infringement '
                                      'is a violation of the rights of a copyright holder, when material whose use is '
                                      'restricted by copyright is used without consent.'), \
           doc_factory.create('doc2',
                              'Plagiarism is also considered a moral offense against anyone who has provided the '
                              'plagiarist with a benefit in exchange for what is specifically supposed to be original '
                              'content. Plagiarism is not the same as copyright infringement. Acts of plagiarism may '
                              'sometimes also form part of a claim for breach of the plagiarist\'s contract.')


@fixture
def matches(doc_factory):
    doc1, doc2 = doc_factory.create('doc1', 'This is a document.\n'), \
                 doc_factory.create('doc2', 'This also is a document.\n')
    doc1_doc2_matches = DocumentPairMatches()
    doc1_doc2_matches.add(Match(Section(doc1, 0, 5), Section(doc2, 0, 5)))
    doc1_doc2_matches.add(Match(Section(doc1, 5, 10), Section(doc2, 5, 10)))
    doc3, doc4 = doc_factory.create('doc3', 'This is another document.\n'), \
                 doc_factory.create('doc4', 'This also is another document.\n')
    doc3_doc4_matches = DocumentPairMatches()
    doc3_doc4_matches.add(Match(Section(doc3, 2, 6), Section(doc4, 2, 8)))
    return [doc1_doc2_matches, doc3_doc4_matches]
