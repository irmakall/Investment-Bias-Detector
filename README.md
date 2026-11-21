# Investment Bias Detector

An AI-powered investment decision journal that flags cognitive biases in the reasoning behind trades, measured against a hand-labeled dataset.

> **Status:** Planning. Requirements are in [REQUIREMENTS.md](REQUIREMENTS.md). No results yet.
>
> **Not financial advice.** This project analyzes decisions. It never recommends buying, selling or holding anything.

## What it does

Before each buy or sell, I write a short note explaining why. The detector:

- **Flags biases** in the note (FOMO, herd behavior, overconfidence, anchoring, loss aversion, confirmation bias) and quotes the sentence that triggered each flag.
- **Asks reflective questions**, for example: *"What will you do if this drops 20%?"*
- **Computes behavioral metrics** from trade history: holding periods, trade frequency and a disposition-effect proxy (selling winners too early, holding losers too long).

## Why evaluation is the core

Bias detection is subjective. A model that "sounds right" isn't enough, so the project is built around measurement:

- **Labeled test set:** 510 real retail-investor posts from r/WallStreetBets, labeled under a written annotation guideline. Labels were suggested by an LLM (Claude), reviewed by the author and corrected where needed. Corrections were not logged separately, so the share of changed suggestions is not reported.
- **Rare biases oversampled:** keyword strata make sure each evaluated bias has enough examples. The set therefore does not follow WSB's natural class distribution.
- **Different models for labeling and testing:** the model that suggested labels is never one of the models being evaluated.
- **Baseline comparison:** the LLM agent is compared to a TF-IDF + logistic regression baseline on accuracy (macro-F1), cost and latency.
- **No leakage:** synthetic data is used only for training, never for testing, and an automated check enforces this.
- **Domain shift:** results are reported separately for public posts and my own decision notes.
- **Reproducible:** the full evaluation runs with one command.

## Results

_Coming after milestone M2._

| Model | Macro-F1 (posts) | Macro-F1 (own notes) | Cost / item | p95 latency |
| :--- | :--- | :--- | :--- | :--- |
| TF-IDF + LR baseline | – | – | – | – |
| LLM agent | – | – | – | – |

## Reproducing the dataset

The raw WSB files go in `data/raw/` (git-ignored, see [data/SOURCES.md](data/SOURCES.md)). Then, from the repo root:

```bash
pip install -r requirements.txt
python -m src.data.sample pilot      # 50-post pilot
python -m src.data.sample main       # 320-post main sample (general + keyword strata)
python -m src.data.sample topup      # 140-post top-up for rare biases
python -m src.data.labels validate   # check labels against the guideline
python -m src.data.labels export     # write data/labels/ (IDs + labels, no text)
pytest
```

The code follows the three steps of the pipeline: `src/data/load.py` (load and filter), `src/data/sample.py` (sampling) and `src/data/labels.py` (labeling rules, checks, export).

The same seed always produces the same samples.

## Design principles

- **Numbers from code, words from the LLM.** Every metric is computed in Python. The LLM only explains numbers it is given, and code checks that it didn't invent any.
- **Evidence-grounded flags.** Each flagged bias cites a span from the note. Code verifies that the span exists.
- **Visible agent loop.** A hand-written function-calling loop with no agent framework, so every prompt is inspectable during eval.
- **Privacy.** The public demo uses a fictional portfolio. Real trades never leave the private environment.
- **Narrow and deep.** Few features, each finished and measured.

## Tech stack

Python · Pydantic · scikit-learn · pandas · Supabase (Postgres) · Streamlit

Post-MVP: pgvector (semantic search), LangGraph (comparison with the hand-written loop).

## Roadmap

| Milestone | Scope | Status |
| :--- | :--- | :--- |
| M1 | Bias definitions, annotation guideline, pilot, model-assisted labeled dataset | 🔄 In progress |
| M2 | LLM bias analyzer, baseline, one-command eval, error analysis | ⏳ Planned |
| M3 | Decision journal, CSV trade import, behavioral metrics, Streamlit UI | ⏳ Planned |
| M4 | Semantic search over past decisions (RAG), Recall@5 | Post-MVP |
| M5 | Outcome tracking | Post-MVP |
| M6 | LangGraph re-implementation and comparison | Post-MVP |

## License

- **Code:** MIT
- **Labels and annotation guideline:** CC-BY-4.0
- **Source posts:** not redistributed. They belong to their authors and come from existing public datasets. See [data/SOURCES.md](data/SOURCES.md) for sources, licenses and platform terms.
