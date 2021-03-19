from plagdef.model.reporting import generate_text_report, generate_xml_reports


def test_generate_text_report_with_no_matches_returns_msg():
    report = generate_text_report([])
    assert report == 'There are no matching text sections in given documents.'


def test_generate_text_report_starts_with_intro(matches):
    report = generate_text_report(matches)
    assert report.startswith(
        'Reporting matches for each pair like this:\n'
        f'  Match(Section(offset, length), Section(offset, length))\n\n')


def test_generate_text_report_contains_matches(matches):
    report = generate_text_report(matches)
    assert 'Pair(doc1, doc2):\n' \
           '  Match(Section(0, 5), Section(0, 5))\n' \
           '  Match(Section(5, 10), Section(5, 10))\n' \
           'Pair(doc3, doc4):\n' \
           '  Match(Section(2, 6), Section(2, 8))\n' in report


def test_generate_xml_reports_with_no_matches_produces_no_report():
    reports = generate_xml_reports([])
    assert len(reports) == 0


def test_generate_xml_reports(matches):
    reports = generate_xml_reports(matches)
    assert len(reports) == 2
    assert reports[0].format, reports[1].format == 'xml'
    assert reports[0].content == \
           '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n' \
           '<report doc1="doc1" doc2="doc2">\n' \
           '  <match doc1_offset="0" doc1_length="5" doc2_offset="0" doc2_length="5"/>\n' \
           '  <match doc1_offset="5" doc1_length="10" doc2_offset="5" doc2_length="10"/>\n' \
           '</report>\n'
    assert reports[1].content == \
           '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n' \
           '<report doc1="doc3" doc2="doc4">\n' \
           '  <match doc1_offset="2" doc1_length="6" doc2_offset="2" doc2_length="8"/>\n' \
           '</report>\n'
