from plagdef.model.reporting import generate_text_report


def test_generate_text_report_with_no_matches_returns_msg():
    report = generate_text_report([])
    assert report == 'No matches found.'


def test_generate_text_report_starts_with_intro(matches):
    report = generate_text_report(matches)
    assert 'Reporting matches for each pair like this:\n' \
           f'  Match(Fragment(start_char, end_char), Fragment(start_char, end_char))\n\n' in report


def test_generate_text_report_contains_plag_type(matches):
    report = generate_text_report(matches)
    assert 'Verbatim matches:\n' in report


def test_generate_text_report_contains_matches(matches):
    report = generate_text_report(matches)
    assert "Pair('path/to/doc1', 'path/to/doc2'):\n" in report or "Pair('path/to/doc2', 'path/to/doc1'):\n" in report
    assert 'Match(Fragment(0, 5), Fragment(0, 5))\n' in report
    assert 'Match(Fragment(5, 10), Fragment(5, 10))\n' in report
    assert "Pair('path/to/doc3', 'path/to/doc4'):\n" in report or "Pair('path/to/doc4', 'path/to/doc3'):\n" in report
    assert 'Match(Fragment(2, 6), Fragment(2, 8))\n' in report \
           or 'Match(Fragment(2, 8), Fragment(2, 6))\n' in report
