"""Step 1 of the data pipeline: project paths, loading WSB data and basic filters.

Used by sample.py (sampling) and labels.py (labeling).
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths, resolved from this file so commands work from any directory
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"          # git-ignored: source texts and working files
DRAFTS_DIR = RAW_DIR / "drafts"          # git-ignored: per-batch suggestion files
LABELS_DIR = ROOT / "data" / "labels"    # committed: labels without any post text

POSTS_FILE = RAW_DIR / "wsb-aug-2021-posts.csv"
COMMENTS_FILE = RAW_DIR / "wsb-aug-2021-comments.csv"
PILOT_FILE = RAW_DIR / "pilot_50.csv"
MAIN_FILE = RAW_DIR / "main_sample.csv"
TOPUP_FILE = RAW_DIR / "topup_sample.csv"
PILOT_LABELS_FILE = RAW_DIR / "pilot_labeling_irmak.csv"
REVIEW_FILE = RAW_DIR / "review_all_irmak.csv"

# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

REMOVED_MARKERS = {"[removed]", "[deleted]"}


def load_posts() -> pd.DataFrame:
    df = pd.read_csv(POSTS_FILE, usecols=["id", "title", "selftext"])
    # A removed/deleted body still leaves the title, which can carry the reasoning.
    body = df["selftext"].fillna("").where(~df["selftext"].isin(REMOVED_MARKERS), "")
    df["text"] = (df["title"].fillna("") + "\n\n" + body).str.strip()
    df["source_type"] = "post"
    return df[["id", "source_type", "text"]]


def load_comments() -> pd.DataFrame:
    # The comments file is large (~1M rows), so only the needed columns are loaded.
    df = pd.read_csv(COMMENTS_FILE, usecols=["id", "body"])
    df = df[~df["body"].isin(REMOVED_MARKERS)]
    df = df.rename(columns={"body": "text"})
    df["text"] = df["text"].fillna("").str.strip()
    df["source_type"] = "comment"
    return df[["id", "source_type", "text"]]


# ---------------------------------------------------------------------------
# Basic filters
# ---------------------------------------------------------------------------

MIN_WORDS = 5        # REQ-003
MAX_CHARS = 1500     # keeps labeling under ~1 minute per item
# Bot messages that are unique per post, so deduplication alone misses them.
BOT_PATTERNS = r"\*\*User Report\*\*|I am a bot"


def base_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Keep texts within the length limits that are not known bot messages."""
    n_words = df["text"].str.split().str.len()
    df = df[(n_words >= MIN_WORDS) & (df["text"].str.len() <= MAX_CHARS)]
    return df[~df["text"].str.contains(BOT_PATTERNS, regex=True)]


def matches(df: pd.DataFrame, pattern: str) -> pd.Series:
    """Boolean mask: does the lowercased text match the regex pattern?"""
    return df["text"].str.lower().str.contains(pattern, regex=True)


def drop_repeated(df: pd.DataFrame) -> pd.DataFrame:
    """Drop every text that appears more than once, not just the extra copies.

    Repeated texts are almost always bots, AutoModerator templates or copypasta.
    Texts are normalized first so "Buy now" and " buy now" count as the same.
    """
    normalized = df["text"].str.lower().str.split().str.join(" ")
    return df[~normalized.duplicated(keep=False)]
