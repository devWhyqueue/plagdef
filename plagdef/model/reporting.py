from __future__ import annotations

from plagdef.model.models import DocumentPairMatches, MatchType


def generate_text_report(matches: list[DocumentPairMatches]) -> str:
    report = ''
    for match_type in MatchType:
        wrote_heading = False
        for doc_pair_matches in matches:
            typed_matches = doc_pair_matches.list(match_type)
            if len(typed_matches):
                if not wrote_heading:
                    report += f'{str(match_type).capitalize()} matches:\n'
                    wrote_heading = True
                report += f"  Pair('{doc_pair_matches.doc1.path}', '{doc_pair_matches.doc2.path}'):\n"
                for match in sorted(typed_matches, key=lambda m: m.frag_from_doc(doc_pair_matches.doc1).start_char):
                    frag1, frag2 = match.frag_from_doc(doc_pair_matches.doc1), match.frag_from_doc(
                        doc_pair_matches.doc2)
                    report += f'    Match(Fragment({frag1.start_char}, {frag1.end_char}), Fragment(' \
                              f'{frag2.start_char}, {frag2.end_char}))\n'
    intro = 'No matches found.'
    if report:
        intro = f'Found {len(matches) if len(matches) else "no"} suspicious document pair' \
                f'{"s" if len(matches) > 1 else ""}.\n' \
                'Reporting matches for each pair like this:\n' \
                f'  Match(Fragment(start_char, end_char), Fragment(start_char, end_char))\n\n'
    return intro + report
