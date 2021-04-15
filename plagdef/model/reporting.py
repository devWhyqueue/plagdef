from __future__ import annotations

from dataclasses import dataclass

from lxml import etree
from lxml.builder import E

from plagdef.model.models import DocumentPairMatches
from plagdef.model.preprocessing import Document


@dataclass(frozen=True)
class DocumentPairReport:
    doc1: Document
    doc2: Document
    content: str
    format: str


def generate_text_report(matches: list[DocumentPairMatches]) -> str:
    doc_pair_reports = []
    for doc_pair_matches in matches:
        doc1, doc2 = doc_pair_matches.doc_pair
        report = f'Pair({doc1.name}, {doc2.name}):\n'
        for match in sorted(doc_pair_matches.list(), key=lambda m: m.frag_from_doc(doc1).start_char):
            frag1, frag2 = match.frag_from_doc(doc1), match.frag_from_doc(doc2)
            report += f'  Match(Fragment({frag1.start_char}, {frag1.end_char}), Fragment({frag2.start_char},' \
                      f' {frag2.end_char}))\n'

        doc_pair_reports.append(DocumentPairReport(doc1, doc2, report, 'txt'))
    intro = 'There are no matching text sections in given documents.'
    if doc_pair_reports:
        intro = 'Reporting matches for each pair like this:\n' \
                f'  Match(Fragment(start_char, end_char), Fragment(start_char, end_char))\n\n'
    return intro + ''.join(f'{doc_pair_report.content}' for doc_pair_report in doc_pair_reports)


def generate_xml_reports(matches: list[DocumentPairMatches]) -> list[DocumentPairReport]:
    doc_pair_reports = []
    for doc_pair_matches in matches:
        doc1, doc2 = doc_pair_matches.doc_pair
        root = E.report(doc1=doc1.name, doc2=doc2.name)
        for match in sorted(doc_pair_matches.list(), key=lambda m: m.frag_from_doc(doc1).start_char):
            frag1, frag2 = match.frag_from_doc(doc1), match.frag_from_doc(doc2)
            root.append(E.match(
                doc1_start_char=str(frag1.start_char), doc1_end_char=str(frag1.end_char),
                doc2_start_char=str(frag2.start_char), doc2_end_char=str(frag2.start_char)
            ))
        report = etree.tostring(root, xml_declaration=True, encoding='UTF-8', pretty_print=True).decode('utf8')
        doc_pair_reports.append(DocumentPairReport(doc1, doc2, report, 'xml'))
    return doc_pair_reports
