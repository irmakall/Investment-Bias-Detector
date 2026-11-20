"""Step 2 of the data pipeline: choosing which posts get labeled.

Usage:
    python -m src.data.sample pilot    # 50 posts: 25 posts + 25 comments (REQ-004)
    python -m src.data.sample main     # 320 posts: general + keyword strata (REQ-003)
    python -m src.data.sample topup    # 140 posts: keyword strata for rare biases (REQ-003)

How sampling works:
    1. decision_candidates  keep decision posts (length, bots, first person + trading term, no repeats)
    2. exclude_ids          drop posts already used in an earlier sample
    3. assign_strata        put each post in a "box" (stratum) by its keywords
    4. sample_by_stratum    draw a fixed number of posts from each box at random (fixed seed)

Keywords only decide which posts get sampled; they never assign labels. Patterns
used by a sample that has been labeled are frozen: changing them changes which
posts the seed selects.
"""

import argparse

import pandas as pd

from src.data.load import (MAIN_FILE, PILOT_FILE, TOPUP_FILE, base_filter, drop_repeated,
                           load_comments, load_posts, matches)

SEED = 42   # same seed -> same samples on every run (REQ-017)

# ---------------------------------------------------------------------------
# Keyword patterns (regex, matched against lowercased text)
# ---------------------------------------------------------------------------

# Decision pre-filter: first person AND a trading action or position.
FIRST_PERSON = r"\b(?:i|i'm|im|i've|ive|i'll|my|me)\b"
DECISION_TERMS = (
    r"\b(?:bought|buying|buy in|sold|selling|sell|holding|hold|added|adding|"
    r"averag(?:e|ed|ing) down|load(?:ed|ing) up|yolo'?d|all in|went in|"
    r"cut my loss(?:es)?|took profits?|taking profits?|trimmed|exited|"
    r"position|calls|puts|shares|cost basis|entry)\b"
)

FOMO = (
    r"before it'?s too late|last chance|can'?t miss|don'?t want to miss|"
    r"not missing (?:out|this|the next)|missing out|\bfomo\b|left behind|"
    r"miss(?:ed)? the (?:boat|train|run)|get in (?:now|before)"
)
ANCHORING = (
    r"from (?:the )?ath|all[- ]time high|down \d+ ?% from|used to be (?:at )?\$?\d|"
    r"cheaper than|at a discount|on sale|bargain|\bsteal\b"
)
# Broad version, used in the main sample. "bag hold" turned out to mostly mean
# "I'm at a loss" rather than loss aversion, so the top-up uses a tighter list.
LOSS_AVERSION_BROAD = (
    r"back to even|break ?even|\bbag ?hold|not selling until|won'?t sell until|"
    r"until i'?m (?:back )?green|not a loss (?:until|if)|only a loss if|"
    r"make it back|get my money back|unrealized loss"
)
LOSS_AVERSION = (
    r"break ?even|back to even|not selling until|won'?t sell until|"
    r"until i'?m (?:back )?green|till (?:it'?s|they'?re|i'?m) green|"
    r"only a loss if|not a loss (?:until|if)|make it back|get my money back"
)
OVERCONFIDENCE = (
    r"guaranteed|can'?t lose|cannot lose|free money|easy money|sure thing|no[- ]brainer|"
    r"literally can'?t|100 ?% (?:going|gonna|will)|easiest (?:trade|money|play)|"
    r"entire (?:savings|account|portfolio|net worth)|life savings|maxed? out (?:my )?margin|"
    r"(?:fully )?on margin|took (?:out )?a loan|(?:gonna|going to|will) moon"
)

# ---------------------------------------------------------------------------
# Sample settings
# ---------------------------------------------------------------------------

PILOT_PER_SOURCE = 25

# Strata are checked in this order; a post goes to the first one it matches.
MAIN_STRATA = {"fomo": FOMO, "loss_aversion": LOSS_AVERSION_BROAD, "anchoring": ANCHORING}
MAIN_SIZES = {"general": 140, "fomo": 60, "loss_aversion": 60, "anchoring": 60}

TOPUP_STRATA = {"overconfidence": OVERCONFIDENCE, "loss_aversion": LOSS_AVERSION, "anchoring": ANCHORING}
TOPUP_SIZES = {"overconfidence": 60, "loss_aversion": 50, "anchoring": 30}

OUTPUT_COLUMNS = ["id", "source_type", "stratum", "text"]

# ---------------------------------------------------------------------------
# Sampling steps
# ---------------------------------------------------------------------------


def decision_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """Step 1: length/bot filter, then the decision pre-filter, then drop repeated texts."""
    df = base_filter(df)
    df = df[matches(df, FIRST_PERSON) & matches(df, DECISION_TERMS)]
    return drop_repeated(df)


def exclude_ids(df: pd.DataFrame, used_files: list) -> pd.DataFrame:
    """Step 2: remove posts that already appear in earlier samples."""
    used = set().union(*(set(pd.read_csv(f)["id"]) for f in used_files))
    return df[~df["id"].isin(used)].copy()


def assign_strata(df: pd.DataFrame, strata: dict, default=None) -> pd.DataFrame:
    """Step 3: add a `stratum` column. A post goes to the first listed stratum it matches."""
    df = df.copy()
    df["stratum"] = default
    for name in reversed(list(strata)):   # reversed, so the first listed stratum wins
        df.loc[matches(df, strata[name]), "stratum"] = name
    return df


def sample_by_stratum(df: pd.DataFrame, sizes: dict, seed: int) -> pd.DataFrame:
    """Step 4: draw `sizes[name]` posts from each stratum, then shuffle so strata are mixed."""
    parts = []
    for name, n in sizes.items():
        pool = df[df["stratum"] == name]
        print(f"{name:15s} pool {len(pool):6,} -> sample {n}")
        parts.append(pool.sample(n=n, random_state=seed))
    out = pd.concat(parts, ignore_index=True)
    out = out.sample(frac=1, random_state=seed).reset_index(drop=True)
    return out[OUTPUT_COLUMNS]


# ---------------------------------------------------------------------------
# The three samples
# ---------------------------------------------------------------------------


def sample_pilot() -> None:
    """25 posts + 25 comments, filtered per source. No strata."""
    parts = []
    for name, loader in [("posts", load_posts), ("comments", load_comments)]:
        raw = loader()
        df = decision_candidates(raw)
        print(f"{name}: {len(raw):,} loaded -> {len(df):,} after cleaning")
        parts.append(df.sample(n=PILOT_PER_SOURCE, random_state=SEED))
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(PILOT_FILE, index=False)
    print(f"Saved {len(out)} items to {PILOT_FILE}")


def sample_main() -> None:
    """General stratum plus keyword strata. Posts matching no keyword go to `general`."""
    df = decision_candidates(pd.concat([load_posts(), load_comments()], ignore_index=True))
    df = exclude_ids(df, [PILOT_FILE])
    df = assign_strata(df, MAIN_STRATA, default="general")
    out = sample_by_stratum(df, MAIN_SIZES, SEED)
    out.to_csv(MAIN_FILE, index=False)
    print(f"Saved {len(out)} items to {MAIN_FILE}")


def sample_topup() -> None:
    """Keyword strata only, for classes that stayed below 20 after the main sample."""
    df = decision_candidates(pd.concat([load_posts(), load_comments()], ignore_index=True))
    df = exclude_ids(df, [PILOT_FILE, MAIN_FILE])
    df = assign_strata(df, TOPUP_STRATA)   # posts matching no keyword are never sampled
    out = sample_by_stratum(df, TOPUP_SIZES, SEED)
    out.to_csv(TOPUP_FILE, index=False)
    print(f"Saved {len(out)} items to {TOPUP_FILE}")


COMMANDS = {"pilot": sample_pilot, "main": sample_main, "topup": sample_topup}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw a labeling sample from the WSB data.")
    parser.add_argument("which", choices=COMMANDS)
    COMMANDS[parser.parse_args().which]()
