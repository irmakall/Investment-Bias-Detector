"""Classical ML baseline (REQ-015): TF-IDF + multiclass logistic regression.

Usage:
    python -m src.eval.baseline

Trained on train only, scored once on test. Settings are fixed up front and are
not tuned on the test set, so the test score stays an honest estimate.
"""

import time

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from src.data.labels import EVALUATED_LABELS, NO_BIAS
from src.data.split import SEED
from src.eval.dataset import load_split

LABELS = sorted(EVALUATED_LABELS | {NO_BIAS})   # fixed order for reports and the confusion matrix


def build_model() -> Pipeline:
    """TF-IDF features + logistic regression in one Pipeline.

    A Pipeline makes fit() learn the vocabulary and IDF from train only,
    so no information from the test set leaks into the features.
    """
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=SEED)),
    ])


def macro_f1(y_true, y_pred) -> float:
    """Macro-F1 over the labels that actually occur in y_true.

    A stratum subset may not contain every class; counting a missing class as F1 = 0
    would punish the model for something it was never tested on.
    """
    present = sorted(set(y_true))
    return f1_score(y_true, y_pred, labels=present, average="macro", zero_division=0)


def evaluate(test: pd.DataFrame, y_pred) -> None:
    """Print per-class scores, the confusion matrix and macro-F1 per stratum group."""
    y_true = test["label"]
    print(classification_report(y_true, y_pred, labels=LABELS, zero_division=0, digits=3))

    matrix = pd.DataFrame(confusion_matrix(y_true, y_pred, labels=LABELS),
                          index=[f"true {l}" for l in LABELS], columns=LABELS)
    print("Confusion matrix (rows = gold, columns = predicted):")
    print(matrix, "\n")

    # general = random sample, keyword = keyword strata (main + top-up), pilot = pilot posts
    group = test["stratum"].where(test["stratum"].isin(["general", "pilot"]), "keyword")
    print("Macro-F1 by stratum group:")
    for name in ["general", "keyword", "pilot"]:
        mask = (group == name).to_numpy()
        print(f"  {name:8s} n={mask.sum():3d}  macro-F1={macro_f1(y_true[mask], y_pred[mask]):.3f}")


def top_features(model: Pipeline, n: int = 10) -> None:
    """Print the n words/bigrams with the highest weight for each class.

    Shows what the model actually relies on, which feeds the error analysis (REQ-018).
    """
    words = model.named_steps["tfidf"].get_feature_names_out()
    clf = model.named_steps["clf"]
    print(f"Top {n} features per class:")
    for label, weights in zip(clf.classes_, clf.coef_):   # one weight row per class
        top = weights.argsort()[::-1][:n]                    # indices of the largest weights
        print(f"  {label:15s} " + ", ".join(words[top]))


def train_and_predict(train: pd.DataFrame, test: pd.DataFrame) -> tuple:
    """Fit on train, predict test. Returns (model, y_pred, fit_s, predict_s). Used by run.py too."""
    model = build_model()

    start = time.perf_counter()
    model.fit(train["text"], train["label"])
    fit_s = time.perf_counter() - start

    start = time.perf_counter()
    y_pred = model.predict(test["text"])
    predict_s = time.perf_counter() - start
    return model, y_pred, fit_s, predict_s


def main() -> None:
    df = load_split()
    train, test = df[df["split"] == "train"], df[df["split"] == "test"]
    model, y_pred, fit_s, predict_s = train_and_predict(train, test)

    print(f"train n={len(train)}  test n={len(test)}  fit {fit_s:.2f}s  predict {predict_s * 1000:.1f}ms\n")
    evaluate(test, y_pred)
    print(f"\nMacro-F1 (test): {macro_f1(test['label'], y_pred):.3f}\n")
    top_features(model)


if __name__ == "__main__":
    main()
