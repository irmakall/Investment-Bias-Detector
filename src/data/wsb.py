"""Shared loading and filtering for the SocialGrep WSB August 2021 dataset."""

from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
POSTS_FILE = RAW_DIR / "wsb-aug-2021-posts.csv"
COMMENTS_FILE = RAW_DIR / "wsb-aug-2021-comments.csv"

MIN_WORDS = 5        # REQ-003
MAX_CHARS = 1500     # keeps labeling under ~1 minute per item
REMOVED_MARKERS = {"[removed]", "[deleted]"}
# Bot messages that are unique per post (so deduplication alone misses them).
BOT_PATTERNS = r"\*\*User Report\*\*|I am a bot"

# Decision pre-filter: the author speaks in first person AND mentions a trading
# action or position. Raises the share of posts that contain the author's own
# decision. Side effect (documented in the README): the dataset only represents
# posts that use this kind of language.
FIRST_PERSON = r"\b(?:i|i'm|im|i've|ive|i'll|my|me)\b"
DECISION_TERMS = (
    r"\b(?:bought|buying|buy in|sold|selling|sell|holding|hold|added|adding|"
    r"averag(?:e|ed|ing) down|load(?:ed|ing) up|yolo'?d|all in|went in|"
    r"cut my loss(?:es)?|took profits?|taking profits?|trimmed|exited|"
    r"position|calls|puts|shares|cost basis|entry)\b"
)


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


def base_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Length limits and known bot messages."""
    n_words = df["text"].str.split().str.len()
    df = df[(n_words >= MIN_WORDS) & (df["text"].str.len() <= MAX_CHARS)]
    return df[~df["text"].str.contains(BOT_PATTERNS, regex=True)]


def matches(df: pd.DataFrame, pattern: str) -> pd.Series:
    return df["text"].str.lower().str.contains(pattern, regex=True)


def drop_repeated(df: pd.DataFrame) -> pd.DataFrame:
    """Drop every text that appears more than once, not just the extra copies.

    Repeated texts are almost always bots, AutoModerator templates or copypasta.
    Texts are normalized first so "Buy now" and " buy now" count as the same.
    """
    normalized = df["text"].str.lower().str.split().str.join(" ")
    return df[~normalized.duplicated(keep=False)]
