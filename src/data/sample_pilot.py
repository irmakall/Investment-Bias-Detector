"""Sample the 50-post pilot set (REQ-004) from the SocialGrep WSB August 2021 dataset.

Usage (from the repo root):
    python src/data/sample_pilot.py

Output: data/raw/pilot_50.csv  (git-ignored; texts are never committed)
"""

import warnings

import pandas as pd

from wsb import (DECISION_TERMS, FIRST_PERSON, RAW_DIR, base_filter, drop_repeated,
                 load_comments, load_posts, matches)

warnings.filterwarnings("ignore", message="This pattern is interpreted as a regular expression")

OUTPUT_FILE = RAW_DIR / "pilot_50.csv"
SEED = 42            # same seed -> same sample on every run (REQ-017)
N_PER_SOURCE = 25    # 25 posts + 25 comments


def main() -> None:
    parts = []
    for name, loader in [("posts", load_posts), ("comments", load_comments)]:
        raw = loader()
        df = base_filter(raw)
        df = df[matches(df, FIRST_PERSON) & matches(df, DECISION_TERMS)]
        df = drop_repeated(df)
        print(f"{name}: {len(raw):,} loaded -> {len(df):,} after cleaning")
        parts.append(df.sample(n=N_PER_SOURCE, random_state=SEED))

    pilot = pd.concat(parts, ignore_index=True)
    pilot.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(pilot)} items to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
