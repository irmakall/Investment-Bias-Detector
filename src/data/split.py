"""Step 4 of the data pipeline: a fixed train/test split of the labeled set (REQ-007).

Usage:
    python -m src.data.split write     # write data/splits/ (refuses if the split is frozen)
    python -m src.data.split check     # recompute the test hash and compare it with split_meta.json
    python -m src.data.split freeze    # run once, after the first eval run: locks the test list

Input:  data/labels/irmak.csv (labels only, no post text)
Output: data/splits/train_ids.txt, test_ids.txt, split_meta.json (committed: IDs only, no text)

Rules:
- Only the evaluated labels (EVALUATED_LABELS + no_bias) count. herd/confirmation are dropped.
- Single-label: each row has exactly one label, and the split is stratified by that label.
- Same seed -> same files. Once frozen, the test list never changes.

"""

import argparse
import hashlib
import json
import sys
from datetime import date

import pandas as pd
from sklearn.model_selection import train_test_split

from src.data.labels import EVALUATED_LABELS, NO_BIAS, read_labeled, split
from src.data.load import LABELS_DIR, ROOT

LABELS_FILE = LABELS_DIR / "irmak.csv"
SPLITS_DIR = ROOT / "data" / "splits"
TRAIN_FILE = SPLITS_DIR / "train_ids.txt"
TEST_FILE = SPLITS_DIR / "test_ids.txt"
META_FILE = SPLITS_DIR / "split_meta.json"

SEED = 42
TEST_SIZE = 0.3
EVAL_LABELS = EVALUATED_LABELS | {NO_BIAS}

# ---------------------------------------------------------------------------
# Building the eval set
# ---------------------------------------------------------------------------


def load_eval_items(path=LABELS_FILE) -> pd.DataFrame:
    """Labeled rows whose label is evaluated. Columns: id, label.

    herd/confirmation rows are dropped. A row with more than one label is an error,
    because the dataset is single-label (guideline v0.3).
    """
    df = read_labeled(path)
    df = df[df["status"] == "labeled"]
    multi = df[df["labels"].map(split).str.len() != 1]
    if not multi.empty:
        raise ValueError(f"{len(multi)} rows do not have exactly one label: {multi['id'].tolist()}")
    df = df[df["labels"].isin(EVAL_LABELS)]
    return df[["id", "labels"]].rename(columns={"labels": "label"}).reset_index(drop=True)



# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------


def make_split(items: pd.DataFrame, seed: int = SEED, test_size: float = TEST_SIZE) -> tuple:
    """Return (train_ids, test_ids), each a sorted list of strings."""
    train_ids, test_ids = train_test_split(items["id"], test_size=test_size, stratify=items["label"],
                                           random_state=seed)
    return sorted(train_ids), sorted(test_ids)


def ids_hash(ids: list) -> str:
    """SHA-256 fingerprint of an ID list. Same IDs in any order -> same hash."""
    text = "\n".join(sorted(ids))


    return hashlib.sha256(text.encode()).hexdigest()


def class_counts(items: pd.DataFrame, ids: list) -> dict:
    """Per-label row counts for the given IDs."""
    rows = items[items["id"].isin(ids)]
    counts = rows["label"].value_counts()
    return {label: int(n) for label, n in sorted(counts.items())}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def read_meta() -> dict:
    return json.loads(META_FILE.read_text()) if META_FILE.exists() else {}


def write() -> None:
    if read_meta().get("frozen"):
        sys.exit("Split is frozen (test set already used in an eval run). Not overwriting.")

    items = load_eval_items()
    train_ids, test_ids = make_split(items)
    shared = set(train_ids) & set(test_ids)


    if shared:
        sys.exit(f"Leakage: {len(shared)} IDs are in both train and test.")
    if set(train_ids) | set(test_ids) != set(items["id"]):
        sys.exit("Some rows are in neither train nor test.")

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_FILE.write_text("\n".join(train_ids) + "\n")
    TEST_FILE.write_text("\n".join(test_ids) + "\n")

    train_counts, test_counts = class_counts(items, train_ids), class_counts(items, test_ids)
    test_hash = ids_hash(test_ids)


    meta = {
        "source_file": str(LABELS_FILE.relative_to(ROOT)),
        "seed": SEED,
        "test_size": TEST_SIZE,
        "n_train": len(train_ids),
        "n_test": len(test_ids),
        "train_counts": train_counts,
        "test_counts": test_counts,
        "test_hash": test_hash,
        "frozen": False,
        "created": date.today().isoformat(),
    }
    META_FILE.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"Saved {len(train_ids)} train / {len(test_ids)} test IDs to {SPLITS_DIR}")
    print(pd.DataFrame({"train": train_counts, "test": test_counts}))
    # Expected test column, roughly: no_bias ~47, overconfidence ~14, anchoring ~9, fomo ~8, loss_aversion ~7


def check() -> None:
    """Exit with code 1 if test_ids.txt no longer matches the recorded hash.

    The eval harness (REQ-016) will call this before every run.
    """
    meta = read_meta()
    if not meta:
        sys.exit("No split found. Run: python -m src.data.split write")
    test_ids = TEST_FILE.read_text().split()
    matches = ids_hash(test_ids) == meta["test_hash"]

    if not matches:
        sys.exit("Test set changed since the split was written! Do not trust this eval run.")
    print(f"OK: {len(test_ids)} test IDs, hash matches.")


def freeze() -> None:
    """Run once, after the first eval run. After this, write() refuses to overwrite."""
    meta = read_meta()
    if not meta:
        sys.exit("No split to freeze. Run: python -m src.data.split write")
    meta["frozen"] = True
    meta["frozen_on"] = date.today().isoformat()
    META_FILE.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Frozen. Test hash: {meta['test_hash']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train/test split tools (REQ-007).")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("write")
    commands.add_parser("check")
    commands.add_parser("freeze")
    args = parser.parse_args()
    {"write": write, "check": check, "freeze": freeze}[args.command]()
