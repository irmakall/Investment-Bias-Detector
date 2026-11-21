import pandas as pd

from src.data.labels import validate_row


def row(**kw):
    base = {"status": "labeled", "labels": "", "evidence": "", "skip_reason": "",
            "text": "I am not selling until I am back to even", "guideline_version": "0.2"}
    return pd.Series({**base, **kw})


def test_valid_bias_label():
    assert validate_row(row(labels="loss_aversion", evidence="not selling until")) == []


def test_evidence_must_be_in_text():
    assert validate_row(row(labels="fomo", evidence="last chance"))


def test_no_bias_has_no_evidence():
    assert validate_row(row(labels="no_bias")) == []
    assert validate_row(row(labels="no_bias", evidence="not selling until"))


def test_exactly_one_label():
    assert validate_row(row(labels="loss_aversion|fomo", evidence="not selling until|back to even"))
    assert validate_row(row(labels="no_bias|fomo", evidence="x"))
    assert validate_row(row(status="labeled"))                      # no label at all


def test_unknown_label():
    assert validate_row(row(labels="greed", evidence="not selling until"))


def test_skip_needs_known_reason_and_no_labels():
    assert validate_row(row(status="skip", skip_reason="meme")) == []
    assert validate_row(row(status="skip", skip_reason="boring"))
    assert validate_row(row(status="skip", skip_reason="meme", labels="fomo"))
