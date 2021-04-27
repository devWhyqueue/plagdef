from __future__ import annotations

from dataclasses import dataclass

from lxml import etree
from lxml.builder import E

from plagdef.model.models import DocumentPairMatches, PlagiarismType
from plagdef.model.preprocessing import Document


@dataclass(frozen=True)
class DocumentPairReport:
    doc1: Document
    doc2: Document
    content: str
    format: str


def generate_text_report(matches: dict[PlagiarismType, list[DocumentPairMatches]]) -> str:
    report = ''
    for plag_type, match_list in matches.items():
        report += f'{str(plag_type).capitalize()} matches:\n'
        for doc_pair_matches in match_list:
            doc1, doc2 = doc_pair_matches.doc_pair
            report += f"  Pair('{doc1.path}', '{doc2.path}'):\n"
            for match in sorted(doc_pair_matches.list(), key=lambda m: m.frag_from_doc(doc1).start_char):
                frag1, frag2 = match.frag_from_doc(doc1), match.frag_from_doc(doc2)
                report += f'    Match(Fragment({frag1.start_char}, {frag1.end_char}), Fragment({frag2.start_char},' \
                          f' {frag2.end_char}))\n'
    intro = 'There are no matching text sections in given documents.'
    if report:
        doc_pair_count = sum(len(m) for m in matches.values())
        intro = f'Found {doc_pair_count if len(matches) else "no"} match' \
                f'{"es" if doc_pair_count > 1 else ""}.\n' \
                'Reporting matches for each pair like this:\n' \
                f'  Match(Fragment(start_char, end_char), Fragment(start_char, end_char))\n\n'
    return intro + report


def generate_xml_reports(matches: dict[PlagiarismType, list[DocumentPairMatches]]) -> list[DocumentPairReport]:
    doc_pair_reports = []
    for type_idx, (plag_type, match_list) in enumerate(matches.items()):
        for match_idx, doc_pair_matches in enumerate(match_list):
            doc1, doc2 = doc_pair_matches.doc_pair
            if not type_idx:
                root = E.report(doc1=doc1.path, doc2=doc2.path)
            if not match_idx:
                plag_type_tag = E.type(name=str(plag_type))
                root.append(plag_type_tag)
            for match in sorted(doc_pair_matches.list(), key=lambda m: m.frag_from_doc(doc1).start_char):
                frag1, frag2 = match.frag_from_doc(doc1), match.frag_from_doc(doc2)
                plag_type_tag.append(E.match(
                    doc1_start_char=str(frag1.start_char), doc1_end_char=str(frag1.end_char),
                    doc2_start_char=str(frag2.start_char), doc2_end_char=str(frag2.start_char)
                ))
            report = etree.tostring(root, xml_declaration=True, encoding='UTF-8', pretty_print=True).decode('utf8')
            doc_pair_reports.append(DocumentPairReport(doc1, doc2, report, 'xml'))
    return doc_pair_reports
