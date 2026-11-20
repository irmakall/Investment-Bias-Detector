"""Step 3 of the data pipeline: labeling (guideline rules, review file, checks, export).

Usage:
    python -m src.data.labels build-review [--force]   # merge suggestion batches into one review file
    python -m src.data.labels validate [FILE ...]      # check labels against the guideline (REQ-005)
    python -m src.data.labels export                   # write data/labels/irmak.csv (no post text)

Flow: LLM suggestions (data/raw/drafts/) -> review file -> human review -> validate -> export.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.data.load import DRAFTS_DIR, LABELS_DIR, PILOT_LABELS_FILE, REVIEW_FILE

# ---------------------------------------------------------------------------
# Guideline rules (annotation_guideline.md §2, §3, §6)
# ---------------------------------------------------------------------------

EVALUATED_LABELS = {"overconfidence", "anchoring", "loss_aversion", "fomo"}
TRACKED_LABELS = {"herd", "confirmation"}           # kept in the data, not evaluated
BIAS_LABELS = EVALUATED_LABELS | TRACKED_LABELS
NO_BIAS = "no_bias"
STATUSES = {"labeled", "skip", "unclear"}
SKIP_REASONS = {"question", "news", "meme", "other_person", "no_decision",
                "outcome_only", "sarcasm", "explicit", "other"}


def normalize(text: str) -> str:
    """Lowercase and collapse whitespace, so evidence matching ignores formatting."""
    return " ".join(str(text).lower().split())


def split(value: str) -> list:
    """'fomo|herd' -> ['fomo', 'herd']; '' -> []."""
    return [part for part in str(value).split("|") if part]


def validate_row(row: pd.Series) -> list:
    """Return the list of rule violations for one labeled row (empty list = valid)."""
    errors = []
    status = row["status"]
    labels, evidence = split(row["labels"]), split(row["evidence"])

    if status not in STATUSES:
        return [f"unknown status '{status}'"]

    if status == "labeled":
        if not labels:
            errors.append("labeled row has no labels")
        elif NO_BIAS in labels:
            if len(labels) > 1:
                errors.append("no_bias combined with another label")
            if evidence:
                errors.append("no_bias should have no evidence")
        else:
            if len(labels) > 2:
                errors.append("more than 2 bias labels")
            if len(set(labels)) != len(labels):
                errors.append("duplicate label")
            unknown = set(labels) - BIAS_LABELS
            if unknown:
                errors.append(f"unknown label(s): {sorted(unknown)}")
            if len(evidence) != len(labels):
                errors.append("needs exactly one evidence phrase per label")
            text = normalize(row["text"])
            for phrase in evidence:
                if normalize(phrase) not in text:
                    errors.append(f"evidence not found in text: '{phrase}'")
    else:
        if labels:
            errors.append(f"{status} row should have no labels")
        if status == "skip" and row["skip_reason"] not in SKIP_REASONS:
            errors.append(f"unknown skip_reason '{row['skip_reason']}'")

    if not str(row.get("guideline_version", "")).strip():
        errors.append("missing guideline_version")
    return errors


def read_labeled(path) -> pd.DataFrame:
    """Read a labeling file exactly as saved: every cell as text, empty cells as ''."""
    return pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False, dtype=str)


def changed_suggestions(df: pd.DataFrame) -> pd.Series:
    """True where the reviewer changed the suggested status or labels."""
    return (df["status"] != df["suggested_status"]) | (df["labels"] != df["suggested_labels"])


# ---------------------------------------------------------------------------
# build-review: merge suggestion batches into one review file
# ---------------------------------------------------------------------------

BORDERLINE_MARKERS = "Sınırda|KILAVUZ EKSİĞİ"
REVIEW_COLUMNS = ["row", "sample", "n", "id", "source_type", "stratum", "borderline", "text", "text_tr",
                  "checked", "status", "labels", "evidence", "skip_reason", "notes", "claude_note",
                  "suggested_status", "suggested_labels", "suggested_evidence", "suggested_skip_reason",
                  "suggested_by", "annotator", "guideline_version"]


def build_review(force: bool) -> None:
    """Unchecked borderline rows first, then other unchecked rows, then checked rows.

    Refuses to overwrite an existing review file without --force, because that
    file holds the reviewer's work.
    """
    if REVIEW_FILE.exists() and not force:
        sys.exit(f"{REVIEW_FILE.name} already exists. Use --force to overwrite (this discards review work).")

    parts = [read_labeled(f).assign(sample=sample)
             for sample in ["main", "topup"]
             for f in sorted(DRAFTS_DIR.glob(f"{sample}_batch*_irmak.csv"))]
    df = pd.concat(parts, ignore_index=True)
    if not df["id"].is_unique:
        sys.exit("Duplicate IDs across batch files.")

    df["n"] = df["n"].astype(int)
    df["borderline"] = df["claude_note"].str.contains(BORDERLINE_MARKERS).map({True: "x", False: ""})
    checked = df["checked"] == "x"
    df["_group"] = 1
    df.loc[~checked & (df["borderline"] == "x"), "_group"] = 0
    df.loc[checked, "_group"] = 2
    df = df.sort_values(["_group", "sample", "n"], kind="stable").reset_index(drop=True)
    df.insert(0, "row", range(1, len(df) + 1))
    df[REVIEW_COLUMNS].to_csv(REVIEW_FILE, index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} rows to {REVIEW_FILE}")


# ---------------------------------------------------------------------------
# validate: check every row and print a summary
# ---------------------------------------------------------------------------


def validate_file(path: Path) -> int:
    """Print errors and a summary for one file. Returns the number of errors."""
    df = read_labeled(path)
    checked = df["checked"].str.strip() == "x"
    n_errors = 0
    for _, row in df.iterrows():
        for message in validate_row(row):
            n_errors += 1
            print(f"  ERROR row n={row.get('n', '?')} id={row['id']}: {message}")

    labeled = df[df["status"] == "labeled"]
    counts = labeled["labels"].map(split).explode().value_counts().to_dict()
    print(f"{path.name}: {len(df)} rows | checked {checked.sum()} | to review {(~checked).sum()} | errors {n_errors}")
    print(f"  status: {df['status'].value_counts().to_dict()}")
    print(f"  labels: {counts}")
    if checked.any():
        rate = changed_suggestions(df[checked]).mean()
        print(f"  suggestions changed by reviewer: {rate:.1%} of {checked.sum()} checked rows")
    return n_errors


def validate(files: list) -> None:
    paths = [Path(p) for p in files] or [PILOT_LABELS_FILE, REVIEW_FILE]
    total = sum(validate_file(p) for p in paths)
    sys.exit(1 if total else 0)   # exit code 1 = errors found


# ---------------------------------------------------------------------------
# export: labels without any post text, for git (guideline §7, REQ-010)
# ---------------------------------------------------------------------------

SOURCE = "socialgrep/reddit-wallstreetbets-aug-2021"
EXPORT_COLUMNS = ["id", "source", "source_type", "sample", "stratum", "status", "labels", "skip_reason",
                  "suggested_status", "suggested_labels", "suggested_by", "annotator", "guideline_version"]


def export() -> None:
    """Refuses to export while any row is unchecked or breaks a guideline rule."""
    pilot = read_labeled(PILOT_LABELS_FILE).assign(sample="pilot", stratum="")
    df = pd.concat([pilot, read_labeled(REVIEW_FILE)], ignore_index=True)

    unchecked = (df["checked"].str.strip() != "x").sum()
    invalid = sum(bool(validate_row(row)) for _, row in df.iterrows())
    if unchecked or invalid:
        sys.exit(f"Not exported: {unchecked} unchecked rows, {invalid} invalid rows. "
                 "Run python -m src.data.labels validate for details.")
    if not df["id"].is_unique:
        sys.exit("Not exported: duplicate IDs.")

    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    path = LABELS_DIR / "irmak.csv"
    df.assign(source=SOURCE)[EXPORT_COLUMNS].to_csv(path, index=False)
    print(f"Exported {len(df)} rows to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Labeling tools.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build-review").add_argument("--force", action="store_true")
    commands.add_parser("validate").add_argument("files", nargs="*")
    commands.add_parser("export")
    args = parser.parse_args()

    if args.command == "build-review":
        build_review(args.force)
    elif args.command == "validate":
        validate(args.files)
    else:
        export()
