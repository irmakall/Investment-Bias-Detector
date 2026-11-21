from typing import get_args

import pytest
from pydantic import ValidationError

from src.data.labels import EVALUATED_LABELS, NO_BIAS
from src.llm.schema import Analysis, Check, Label

CHECKLIST = {"thesis", "invalidation", "valuation", "research",
             "position_size", "time_horizon", "opportunity_cost"}   # REQUIREMENTS §4.4


def analysis(**kw):
    base = {"rationale": "Waits to get back to the buy price.", "label": "loss_aversion",
            "evidence": "not selling until", "missing_checks": ["invalidation"],
            "questions": [{"text": "What would make you admit the thesis is wrong?", "check": "invalidation"}]}
    return Analysis(**{**base, **kw})


def test_literals_match_the_rest_of_the_project():
    assert set(get_args(Label)) == EVALUATED_LABELS | {NO_BIAS}
    assert set(get_args(Check)) == CHECKLIST


def test_valid_analysis():
    assert analysis().label == "loss_aversion"
    assert analysis(label="no_bias", evidence=None).evidence is None


def test_unknown_label_is_rejected():
    with pytest.raises(ValidationError):
        analysis(label="herd")


def test_evidence_must_match_label():
    with pytest.raises(ValidationError):
        analysis(evidence=None)                    # bias without evidence
    with pytest.raises(ValidationError):
        analysis(label="no_bias")                  # no_bias with evidence


def test_questions_must_target_missing_checks():
    with pytest.raises(ValidationError):
        analysis(missing_checks=["thesis"])        # question targets invalidation
    with pytest.raises(ValidationError):
        analysis(missing_checks=["invalidation", "invalidation"])
    assert analysis(missing_checks=[], questions=[]).questions == []


def test_at_most_three_questions():
    q = {"text": "Why this stock?", "check": "thesis"}
    with pytest.raises(ValidationError):
        analysis(missing_checks=["thesis"], questions=[q] * 4)


def test_parses_model_json():
    raw = ('{"rationale": "r", "label": "fomo", "evidence": "fomo", '
           '"missing_checks": ["valuation"], "questions": [{"text": "q?", "check": "valuation"}]}')
    assert Analysis.model_validate_json(raw).label == "fomo"
