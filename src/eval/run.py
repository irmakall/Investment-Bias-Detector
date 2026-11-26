"""One-command evaluation (REQ-016): baseline and Gemini on the frozen test set.

Usage:
    export GEMINI_API_KEY=...  GEMINI_MODEL=gemini-3.5-flash-lite
    python -m src.eval.run                 # full run, cached answers are reused (REQ-019)
    python -m src.eval.run --limit 5       # quick try on the first 5 test notes
    python -m src.eval.run --fresh         # ignore the cache and call the API again

Outputs:
    data/results/<run_id>.json   setup + metrics, no post text (committed, REQ-017)
    data/results/latest.md       Markdown table for the README
    data/raw/errors/<run_id>.csv every misclassified note with its text (git-ignored, REQ-018)
    data/raw/llm_cache/*.json    one cached Gemini answer per note (git-ignored, REQ-019)
"""

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from src.data.labels import normalize
from src.data.load import RAW_DIR, ROOT
from src.data.split import SEED, read_meta
from src.eval.baseline import LABELS, macro_f1, train_and_predict
from src.eval.dataset import load_split
from src.llm.gemini import analyze, get_client, get_model
from src.llm.prompt import GUIDELINE_VERSION, PRIORITY_CHECKS, prompt_hash

CACHE_DIR = RAW_DIR / "llm_cache"
ERRORS_DIR = RAW_DIR / "errors"
RESULTS_DIR = ROOT / "data" / "results"
ERROR_LABEL = "__error__"      # prediction used when Gemini gave no valid answer: always counted as wrong

DEFAULT_DELAY_S = 4.0          # pause between API calls (about 15 per minute)
RETRY_WAIT_S = 60.0            # pause after a temporary API error before trying the note again
RETRY_ATTEMPTS = 3

# REQ-013: phrases that turn a question into advice or a verdict on the asset.
ADVICE_PATTERN = re.compile(
    r"\b(you should|should you (buy|sell|hold)|i (would )?recommend|consider (buying|selling|holding)"
    r"|(buy|sell|hold) (it|now|more)\b|take (your )?profits?|cut (your )?loss"
    r"|better opportunit|overvalued|undervalued|too expensive|a good buy)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Gemini with cache
# ---------------------------------------------------------------------------


def cache_key(model: str, text: str) -> str:
    """Same model + same prompt + same note -> same key. A prompt change invalidates the cache."""
    return hashlib.sha256(f"{model}\n{prompt_hash()}\n{text}".encode()).hexdigest()[:20]


TEMPORARY_ERRORS = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")


def is_temporary_error(out: dict) -> bool:
    """Quota (429) and overload (503) errors pass after a wait; invalid answers do not."""
    return "error" in out and any(code in out["error"] for code in TEMPORARY_ERRORS)


def analyze_cached(text: str, client, model: str, fresh: bool, delay_s: float) -> tuple[dict, bool]:
    """Return (answer, came_from_cache). Errors are never cached, so they are retried next run."""
    path = CACHE_DIR / f"{cache_key(model, text)}.json"
    if path.exists() and not fresh:
        return json.loads(path.read_text()), True

    for _ in range(RETRY_ATTEMPTS):
        out = analyze(text, client=client, model=model)
        if not is_temporary_error(out):
            break
        print(f"    temporary API error, waiting {RETRY_WAIT_S:.0f}s ...")
        time.sleep(RETRY_WAIT_S)
    time.sleep(delay_s)

    if "result" in out:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2))
    return out, False


def run_llm(test: pd.DataFrame, fresh: bool, delay_s: float) -> pd.DataFrame:
    """One row per test note: prediction, evidence, questions and call metadata."""
    client, model = get_client(), get_model()
    rows = []
    for i, (note_id, text) in enumerate(zip(test["id"], test["text"]), start=1):
        out, cached = analyze_cached(text, client, model, fresh, delay_s)
        result = out.get("result") or {}
        rows.append({
            "id": note_id,
            "pred": result.get("label", ERROR_LABEL),
            "evidence": result.get("evidence"),
            "missing_checks": result.get("missing_checks", []),
            "questions": result.get("questions", []),
            "error": out.get("error", ""),
            "cached": cached,
            "attempts": out.get("attempts", 0),
            "latency_s": out.get("latency_s", 0.0),
            "input_tokens": out.get("input_tokens", 0),
            "output_tokens": out.get("output_tokens", 0),
        })
        status = "cache" if cached else ("ERROR" if rows[-1]["error"] else "api")
        print(f"  [{i:3d}/{len(test)}] {note_id:10s} {status:5s} -> {rows[-1]['pred']}")
    return pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def classification_metrics(test: pd.DataFrame, y_pred) -> dict:
    """Per-class P/R/F1, macro-F1, confusion matrix and macro-F1 per stratum group (with n)."""
    y_true = test["label"].to_numpy()
    y_pred = np.asarray(y_pred)
    report = classification_report(y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0)
    group = test["stratum"].where(test["stratum"].isin(["general", "pilot"]), "keyword").to_numpy()
    return {
        "macro_f1": round(macro_f1(y_true, y_pred), 4),
        "per_class": {l: {k: round(report[l][k], 4) for k in ("precision", "recall", "f1-score", "support")}
                      for l in LABELS},
        "confusion_matrix": {"labels": LABELS,
                             "rows_gold_cols_pred": confusion_matrix(y_true, y_pred, labels=LABELS).tolist()},
        "by_stratum": {g: {"n": int((group == g).sum()),
                           "macro_f1": round(macro_f1(y_true[group == g], y_pred[group == g]), 4)
                                       if (group == g).any() else None}   # a --limit run may miss a group
                       for g in ["general", "keyword", "pilot"]},
    }


def is_grounded(evidence: str, text: str) -> bool:
    """REQ-012: the evidence must appear in the note (case and whitespace ignored)."""
    return normalize(evidence) in normalize(text)


def flagged_questions(questions: list) -> list:
    """REQ-013: question texts that contain an advice or verdict phrase."""
    return [q["text"] for q in questions if ADVICE_PATTERN.search(q["text"])]


def targets_priority_check(label: str, missing: list, questions: list) -> bool | None:
    """REQ-027: if a priority check of the label is missing, at least one question must target one.

    None = the rule does not apply (no_bias, or no priority check is missing).
    """
    missing_priority = set(PRIORITY_CHECKS.get(label, [])) & set(missing)
    if not missing_priority:
        return None
    return any(q["check"] in missing_priority for q in questions)


def llm_quality(test: pd.DataFrame, llm: pd.DataFrame) -> dict:
    df = llm.merge(test[["id", "text"]], on="id")
    with_evidence = df[df["evidence"].notna() & (df["evidence"] != "")]
    grounded = [is_grounded(e, t) for e, t in zip(with_evidence["evidence"], with_evidence["text"])]
    n_flagged = sum(len(flagged_questions(q)) for q in df["questions"])
    priority = [targets_priority_check(p, m, q) for p, m, q in zip(df["pred"], df["missing_checks"], df["questions"])]
    applicable = [x for x in priority if x is not None]
    return {
        "n_errors": int((df["pred"] == ERROR_LABEL).sum()),
        "n_retried": int((df["attempts"] > 1).sum()),
        "evidence_n": len(grounded),
        "ungrounded_evidence_rate": round(1 - np.mean(grounded), 4) if grounded else None,
        "questions_total": int(sum(len(q) for q in df["questions"])),
        "questions_flagged_advice": int(n_flagged),
        "priority_check_rule_n": len(applicable),
        "priority_check_rule_rate": round(float(np.mean(applicable)), 4) if applicable else None,
    }


def call_stats(llm: pd.DataFrame) -> dict:
    ok = llm[llm["pred"] != ERROR_LABEL]
    return {
        "latency_p50_s": round(float(np.percentile(ok["latency_s"], 50)), 3) if len(ok) else None,
        "latency_p95_s": round(float(np.percentile(ok["latency_s"], 95)), 3) if len(ok) else None,
        "input_tokens_per_item": round(float(ok["input_tokens"].mean()), 1) if len(ok) else None,
        "output_tokens_per_item": round(float(ok["output_tokens"].mean()), 1) if len(ok) else None,
        "n_cached": int(llm["cached"].sum()),
    }

# ---------------------------------------------------------------------------
# Setup record and outputs
# ---------------------------------------------------------------------------


def git_commit() -> str:
    """Current commit, with "-dirty" when there are uncommitted changes."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    commit = git("rev-parse", "--short", "HEAD") or "unknown"
    return commit + ("-dirty" if git("status", "--porcelain") else "")


def setup_record(model: str, n_test: int, limit: int | None) -> dict:
    """REQ-017: everything needed to know what produced these numbers."""
    return {
        "date": datetime.now().isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "llm_model": model,
        "prompt_hash": prompt_hash(),
        "guideline_version": GUIDELINE_VERSION,
        "test_hash": read_meta()["test_hash"],
        "seed": SEED,
        "n_test": n_test,
        "limit": limit,
    }


def _f1(x) -> str:
    """Format a score; "–" for a stratum with no items (possible in a --limit run)."""
    return "–" if x is None else f"{x:.3f}"


def markdown_table(results: dict) -> str:
    b, g = results["baseline"], results["llm"]
    return "\n".join([
        f"Test set: {results['setup']['n_test']} posts · run {results['setup']['date']} · "
        f"commit {results['setup']['git_commit']}",
        "",
        "| Model | Macro-F1 | Macro-F1 (general / keyword) | Latency p50 / p95 | Tokens in / out per item |",
        "| :--- | ---: | :--- | :--- | :--- |",
        f"| TF-IDF + LR baseline | {b['macro_f1']:.3f} | {_f1(b['by_stratum']['general']['macro_f1'])} / "
        f"{_f1(b['by_stratum']['keyword']['macro_f1'])} | {b['predict_ms_per_item']:.2f} ms | – |",
        f"| {results['setup']['llm_model']} (zero-shot) | {g['macro_f1']:.3f} | "
        f"{_f1(g['by_stratum']['general']['macro_f1'])} / {_f1(g['by_stratum']['keyword']['macro_f1'])} | "
        f"{g['latency_p50_s']} s / {g['latency_p95_s']} s | "
        f"{g['input_tokens_per_item']} / {g['output_tokens_per_item']} |",
        "",
        f"LLM: {g['n_errors']} failed answers, ungrounded evidence {g['ungrounded_evidence_rate']}, "
        f"{g['questions_flagged_advice']} of {g['questions_total']} questions flagged as advice, "
        f"priority-check rule met in {g['priority_check_rule_rate']} of {g['priority_check_rule_n']} applicable notes.",
    ]) + "\n"


def save_errors(run_id: str, test: pd.DataFrame, base_pred, llm: pd.DataFrame) -> None:
    """REQ-018: every note either model got wrong, with text, for the error analysis (git-ignored)."""
    df = test[["id", "stratum", "label", "text"]].copy()
    df["baseline_pred"] = base_pred
    df = df.merge(llm[["id", "pred", "evidence", "error"]].rename(columns={"pred": "llm_pred",
                                                                           "evidence": "llm_evidence"}), on="id")
    wrong = df[(df["baseline_pred"] != df["label"]) | (df["llm_pred"] != df["label"])].copy()
    wrong["advice_flags"] = [" | ".join(flagged_questions(q)) for q in
                             llm.set_index("id").loc[wrong["id"], "questions"]]
    wrong["error_category"] = ""          # filled in by hand during the error analysis
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)
    wrong.to_csv(ERRORS_DIR / f"{run_id}.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate baseline and Gemini on the frozen test set.")
    parser.add_argument("--fresh", action="store_true", help="ignore the cache and call the API again")
    parser.add_argument("--limit", type=int, help="only the first N test notes (quick try)")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_S, help="seconds between API calls")
    args = parser.parse_args()

    df = load_split()                                   # also checks the test hash
    train = df[df["split"] == "train"]
    test = df[df["split"] == "test"].reset_index(drop=True)
    if args.limit:
        test = test.head(args.limit)

    print("Baseline ...")
    _, base_pred, _, predict_s = train_and_predict(train, test)
    baseline = classification_metrics(test, base_pred)
    baseline["predict_ms_per_item"] = round(predict_s * 1000 / len(test), 3)

    print(f"Gemini ({get_model()}) on {len(test)} notes ...")
    llm = run_llm(test, args.fresh, args.delay)
    llm_metrics = {**classification_metrics(test, llm["pred"]), **llm_quality(test, llm), **call_stats(llm)}

    setup = setup_record(get_model(), len(test), args.limit)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + setup["llm_model"]
    results = {"setup": setup, "baseline": baseline, "llm": llm_metrics}

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / f"{run_id}.json").write_text(json.dumps(results, indent=2) + "\n")
    table = markdown_table(results)
    if not args.limit:                                  # a partial run must not replace the README table
        (RESULTS_DIR / "latest.md").write_text(table)
    save_errors(run_id, test, base_pred, llm)

    print("\n" + table)
    print(f"Saved data/results/{run_id}.json and data/raw/errors/{run_id}.csv")


if __name__ == "__main__":
    main()
