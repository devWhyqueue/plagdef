from __future__ import annotations

from plagdef.model.legacy import algorithm


def find_matches(doc_repo, config_repo) -> list[algorithm.DocumentPairMatches]:
    return algorithm.find_matches(doc_repo.list(), config_repo.get())
