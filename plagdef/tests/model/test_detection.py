from unittest.mock import MagicMock

from plagdef.model.detection import find_matches
from plagdef.model.legacy import algorithm
from plagdef.tests.fakes import ConfigFakeRepository, DocumentFakeRepository
# noinspection PyUnresolvedReferences
from plagdef.tests.fixtures import config, doc_factory


def test_find_matches(doc_factory, config):
    docs = [doc_factory.create('doc1', 'This is a document.\n'),
            doc_factory.create('doc2', 'This also is a document.\n')]
    doc_repo = DocumentFakeRepository(docs)
    config_repo = ConfigFakeRepository(config)
    algorithm.find_matches = MagicMock()
    find_matches(doc_repo, config_repo)
    algorithm.find_matches.assert_called_with(doc_repo.list(), config_repo.get())
