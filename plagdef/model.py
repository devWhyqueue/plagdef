from ast import literal_eval
from configparser import ConfigParser
from itertools import combinations
from pathlib import Path

from lxml import etree
from lxml.builder import E

from plagdef.algorithm import SGSPLAG
from plagdef.repository import DocumentFileRepository


class MyConfig:
    def __init__(self, config: Path):
        parser = ConfigParser()
        parser.read(config)
        for section in parser.sections():
            typed_config = [(key, literal_eval(val)) for key, val in parser.items(section)]
            self.__dict__.update(dict(typed_config))


class Document:
    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text


class Section:
    def __init__(self, doc: Document, offset: int, length: int):
        self.doc = doc
        self.offset = offset
        self.length = length


class Match:
    def __init__(self, sec1: Section, sec2: Section):
        self.sec1 = sec1
        self.sec2 = sec2


class DocumentPairMatches:
    def __init__(self, doc_pair: tuple[Document]):
        self.doc1 = doc_pair[0]
        self.doc2 = doc_pair[1]
        self._matches = []

    def add(self, match: Match):
        self._matches.append(match)

    def list(self):
        return self._matches

    def empty(self):
        return not self._matches


class Report:
    def __init__(self, matches: list[DocumentPairMatches], out_dir: Path):
        self.matches = matches
        self.out_dir = out_dir

    def text(self):
        report = f'Found {len(self.matches)} suspicious document pairs.\n'
        report += f'Reporting matches for each pair like this:\n'
        report += f'\tMatch(Section(offset, length), Section(offset, length))\n\nSTART REPORT\n---------------\n'
        for doc_pair_matches in self.matches:
            report += f'Pair({doc_pair_matches.doc1.name}, {doc_pair_matches.doc2.name}):\n'
            for match in doc_pair_matches.list():
                report += f'\tMatch(Section({match.sec1.offset}, {match.sec1.offset}), '
                report += f'Section({match.sec2.offset}, {match.sec2.length}))\n'
        report += '---------------\nEND REPORT'
        return report

    def xml(self):
        for doc_pair_matches in self.matches:
            root = E.report(doc1=doc_pair_matches.doc1.name, doc2=doc_pair_matches.doc2.name)
            for match in doc_pair_matches.list():
                root.append(E.detection(
                    doc1_offset=str(match.sec1.offset), doc1_length=str(match.sec1.length),
                    doc2_offset=str(match.sec2.offset), doc2_length=str(match.sec2.length)
                ))
            xml_file = f'{self.out_dir}/{doc_pair_matches.doc1.name}-{doc_pair_matches.doc2.name}.xml'
            etree.ElementTree(root).write(xml_file, xml_declaration=True, encoding='UTF-8', pretty_print=True)


def detect_matches(doc_dir: Path):
    config = MyConfig(Path('settings.ini'))
    docs = DocumentFileRepository(doc_dir)
    matches = []
    for doc1, doc2 in combinations(docs.list(), 2):
        doc_pair_matches = DocumentPairMatches((doc1, doc2))
        sgsplag_obj = SGSPLAG(doc1.text, doc2.text, config)
        type_plag, summary_flag = sgsplag_obj.process()
        for det in sgsplag_obj.detections:
            match = Match(Section(doc1, det[0][0], det[0][1] - det[0][0]),
                          Section(doc2, det[1][0], det[1][1] - det[1][0]))
            doc_pair_matches.add(match)
        if not doc_pair_matches.empty():
            matches.append(doc_pair_matches)
    return matches
