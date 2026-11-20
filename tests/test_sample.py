import pandas as pd
import pytest

from src.data import sample as s
from src.data.load import MAIN_FILE, PILOT_FILE, TOPUP_FILE, matches


def frame(texts):
    return pd.DataFrame({"id": [str(i) for i in range(len(texts))], "text": texts})


def test_decision_prefilter_needs_first_person_and_trading_term():
    df = frame(["I bought more calls today", "Everyone bought calls today", "I think it will rain"])
    mask = matches(df, s.FIRST_PERSON) & matches(df, s.DECISION_TERMS)
    assert mask.tolist() == [True, False, False]


def test_keyword_strata_match_their_targets():
    assert matches(frame(["not selling until I'm back to even"]), s.LOSS_AVERSION).all()
    assert matches(frame(["this is free money"]), s.OVERCONFIDENCE).all()
    assert matches(frame(["it was down 60% from ATH"]), s.ANCHORING).all()
    assert matches(frame(["can't miss this one"]), s.FOMO).all()


def test_first_listed_stratum_wins():
    df = frame(["fomo and I want to break even"])
    assert s.assign_strata(df, s.MAIN_STRATA, default="general")["stratum"].tolist() == ["fomo"]


samples_present = pytest.mark.skipif(
    not all(f.exists() for f in [PILOT_FILE, MAIN_FILE, TOPUP_FILE]),
    reason="sample files are git-ignored and not present",
)


@samples_present
def test_samples_do_not_overlap():
    ids = [set(pd.read_csv(f)["id"]) for f in [PILOT_FILE, MAIN_FILE, TOPUP_FILE]]
    assert not (ids[0] & ids[1]) and not (ids[0] & ids[2]) and not (ids[1] & ids[2])


@samples_present
@pytest.mark.parametrize("path, sizes", [(MAIN_FILE, s.MAIN_SIZES), (TOPUP_FILE, s.TOPUP_SIZES)])
def test_stratum_sizes(path, sizes):
    assert pd.read_csv(path)["stratum"].value_counts().to_dict() == sizes
