"""Shared eval data: labeled posts joined with their text and their train/test split.

Both the baseline (REQ-015) and the LLM eval (REQ-016) load data only through
load_split(), so they are always scored on exactly the same test set.

Nothing is written to disk: the result holds post texts, which must stay out of git.
"""

import numpy as np
import pandas as pd

from src.data.labels import read_labeled
from src.data.load import PILOT_LABELS_FILE, REVIEW_FILE
from src.data.split import LABELS_FILE, TEST_FILE, TRAIN_FILE, check, read_meta

COLUMNS = ["id", "text", "label", "stratum", "split"]


def load_texts() -> pd.DataFrame:
    """id + text for every labeled post (pilot and review files). Columns: id, text."""
    files = [PILOT_LABELS_FILE, REVIEW_FILE]
    texts = pd.concat([read_labeled(f)[["id", "text"]] for f in files], ignore_index=True)
    if not texts["id"].is_unique:
        raise ValueError("The same post ID appears in more than one labeling file.")
    return texts


def load_labels() -> pd.DataFrame:
    """Official labels from data/labels/irmak.csv. Columns: id, label, stratum.

    Pilot posts have no stratum in the export, so they get "pilot".
    """
    df = read_labeled(LABELS_FILE)
    df = df[df["status"] == "labeled"]
    df = df.rename(columns={"labels": "label"})
    df["stratum"] = df["stratum"].replace("", "pilot")
    return df[["id", "label", "stratum"]]


def read_ids(path) -> list:
    return path.read_text().split()


def load_split() -> pd.DataFrame:
    """Train + test posts with text, label, stratum and split. Columns: COLUMNS."""
    check()   # stops if test_ids.txt no longer matches the recorded hash
    train_ids, test_ids = read_ids(TRAIN_FILE), read_ids(TEST_FILE)
    df = load_labels().merge(load_texts(), on="id", how="inner", validate="one_to_one")

    # Keep only split rows (herd/confirmation posts are labeled but in neither list),
    # then mark each one as train or test.
    df = df[df["id"].isin(train_ids + test_ids)].copy()
    df["split"] = np.where(df["id"].isin(train_ids), "train", "test")

    # The counts must match split_meta.json, otherwise the inner merge lost rows silently.
    meta = read_meta()
    expected = {"train": meta["n_train"], "test": meta["n_test"]}
    actual = df["split"].value_counts().to_dict()
    if actual != expected:
        raise ValueError(f"Split sizes differ from split_meta.json: expected {expected}, got {actual}")

    if (df["text"].str.strip() == "").any():
        raise ValueError("Some posts have an empty text.")
    return df[COLUMNS].reset_index(drop=True)


if __name__ == "__main__":
    df = load_split()
    print(pd.crosstab(df["label"], df["split"], margins=True))
    print()
    print(pd.crosstab(df["stratum"], df["split"]))
