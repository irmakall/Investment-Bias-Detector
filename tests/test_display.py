from src.journal.display import highlight_evidence


def test_evidence_is_marked_ignoring_case_and_spaces():
    html = highlight_evidence("I must get in BEFORE   it's too late.", "before it's too late")
    assert html == "I must get in <mark>BEFORE   it&#x27;s too late</mark>."


def test_no_evidence_or_no_match_returns_plain_text():
    assert highlight_evidence("Solid thesis.", None) == "Solid thesis."
    assert highlight_evidence("Solid thesis.", "moon") == "Solid thesis."


def test_note_text_is_escaped():
    html = highlight_evidence("<script>x</script> all in", "all in")
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert html.endswith("<mark>all in</mark>")


def test_newlines_become_line_breaks():
    assert highlight_evidence("a\nb", None) == "a<br>b"


from src.journal.display import with_n


def test_small_samples_are_labeled():
    assert with_n("9.0 days", 2) == "9.0 days (n=2) · insufficient data"
    assert with_n("9.0 days", 12) == "9.0 days (n=12)"
    assert with_n(None, 0) == "– (n=0)"
