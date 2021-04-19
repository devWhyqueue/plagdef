from plagdef.model.reporting import generate_text_report, generate_xml_reports


def test_generate_text_report_with_no_matches_returns_msg():
    report = generate_text_report([])
    assert report == 'There are no matching text sections in given documents.'


def test_generate_text_report_starts_with_intro(matches):
    report = generate_text_report(matches)
    assert report.startswith(
        'Reporting matches for each pair like this:\n'
        f'  Match(Fragment(start_char, end_char), Fragment(start_char, end_char))\n\n')


def test_generate_text_report_contains_matches(matches):
    report = generate_text_report(matches)
    assert "Pair('path/to/doc1', 'path/to/doc2'):\n" in report or "Pair('path/to/doc2', 'path/to/doc1'):\n" in report
    assert 'Match(Fragment(0, 5), Fragment(0, 5))\n' in report
    assert 'Match(Fragment(5, 10), Fragment(5, 10))\n' in report
    assert "Pair('path/to/doc3', 'path/to/doc4'):\n" in report or "Pair('path/to/doc4', 'path/to/doc3'):\n" in report
    assert 'Match(Fragment(2, 6), Fragment(2, 8))\n' in report \
           or 'Match(Fragment(2, 8), Fragment(2, 6))\n' in report


def test_generate_xml_reports_with_no_matches_produces_no_report():
    reports = generate_xml_reports([])
    assert len(reports) == 0


def test_generate_xml_reports(matches):
    reports = generate_xml_reports(matches)
    assert len(reports) == 2
    assert reports[0].format, reports[1].format == 'xml'
    assert reports[0].content.startswith('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n') \
           and reports[1].content.startswith('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
