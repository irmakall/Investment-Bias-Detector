"""Sample the main labeling set (REQ-003) with extra samples for rare biases.

Usage (from the repo root):
    python src/data/sample_main.py

Strata:
    general        decision pre-filter only (natural mix of decision posts)
    fomo           pre-filter + FOMO keywords
    loss_aversion  pre-filter + loss-aversion keywords
    anchoring      pre-filter + anchoring keywords

Keyword strata only decide which posts get *sampled*. They are NOT labels:
a post from the `fomo` stratum is labeled like any other post and may end up
as `no_bias`. Because rare biases are oversampled, the resulting set does not
follow WSB's natural class distribution (stated in the README).

Output: data/raw/main_sample.csv  (git-ignored; texts are never committed)
"""

import warnings

import pandas as pd

from wsb import (DECISION_TERMS, FIRST_PERSON, RAW_DIR, base_filter, drop_repeated,
                 load_comments, load_posts, matches)

warnings.filterwarnings("ignore", message="This pattern is interpreted as a regular expression")

PILOT_FILE = RAW_DIR / "pilot_50.csv"
OUTPUT_FILE = RAW_DIR / "main_sample.csv"
SEED = 42

# Checked in this order; a post goes to the first stratum it matches.
STRATA = {
    "fomo": (
        r"before it'?s too late|last chance|can'?t miss|don'?t want to miss|"
        r"not missing (?:out|this|the next)|missing out|\bfomo\b|left behind|"
        r"miss(?:ed)? the (?:boat|train|run)|get in (?:now|before)"
    ),
    "loss_aversion": (
        r"back to even|break ?even|\bbag ?hold|not selling until|won'?t sell until|"
        r"until i'?m (?:back )?green|not a loss (?:until|if)|only a loss if|"
        r"make it back|get my money back|unrealized loss"
    ),
    "anchoring": (
        r"from (?:the )?ath|all[- ]time high|down \d+ ?% from|used to be (?:at )?\$?\d|"
        r"cheaper than|at a discount|on sale|bargain|\bsteal\b"
    ),
}
SAMPLE_SIZES = {"general": 140, "fomo": 60, "loss_aversion": 60, "anchoring": 60}


def main() -> None:
    df = pd.concat([load_posts(), load_comments()], ignore_index=True)
    df = base_filter(df)
    df = df[matches(df, FIRST_PERSON) & matches(df, DECISION_TERMS)]
    df = drop_repeated(df)

    pilot_ids = set(pd.read_csv(PILOT_FILE)["id"])
    df = df[~df["id"].isin(pilot_ids)].copy()

    df["stratum"] = "general"
    for name in reversed(list(STRATA)):   # reversed, so the first listed stratum wins
        df.loc[matches(df, STRATA[name]), "stratum"] = name

    parts = []
    for name, n in SAMPLE_SIZES.items():
        pool = df[df["stratum"] == name]
        print(f"{name:14s} pool {len(pool):6,} -> sample {n}")
        parts.append(pool.sample(n=n, random_state=SEED))

    out = pd.concat(parts, ignore_index=True)
    out = out.sample(frac=1, random_state=SEED).reset_index(drop=True)  # mix strata
    out[["id", "source_type", "stratum", "text"]].to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(out)} items to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
