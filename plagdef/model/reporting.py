from dataclasses import dataclass

from lxml import etree
from lxml.builder import E

from plagdef.model.legacy.algorithm import DocumentPairMatches
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
        doc1, doc2 = doc_pair_matches.doc1, doc_pair_matches.doc2
        report = f'Pair({doc1.name}, {doc2.name}):\n'
        for match in doc_pair_matches.list():
            report += f'  Match(Section({match.sec1.offset}, {match.sec1.length}), Section({match.sec2.offset},' \
                      f' {match.sec2.length}))\n'

        doc_pair_reports.append(DocumentPairReport(doc1, doc2, report, 'txt'))
    intro = 'There are no matching text sections in given documents.'
    if doc_pair_reports:
        intro = 'Reporting matches for each pair like this:\n' \
                f'  Match(Section(offset, length), Section(offset, length))\n\n'
    return intro + ''.join(f'{doc_pair_report.content}' for doc_pair_report in doc_pair_reports)


def generate_xml_reports(matches: list[DocumentPairMatches], doc_pair_report_repo):
    for doc_pair_matches in matches:
        root = E.report(doc1=doc_pair_matches.doc1.name, doc2=doc_pair_matches.doc2.name)
        for match in doc_pair_matches.list():
            root.append(E.match(
                doc1_offset=str(match.sec1.offset), doc1_length=str(match.sec1.length),
                doc2_offset=str(match.sec2.offset), doc2_length=str(match.sec2.length)
            ))
        report = etree.tostring(root, xml_declaration=True, encoding='UTF-8', pretty_print=True).decode('utf8')
        doc_pair_report_repo.add(DocumentPairReport(doc_pair_matches.doc1, doc_pair_matches.doc2, report, 'xml'))
