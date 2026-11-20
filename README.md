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

- **Hand-labeled test set:** 300–500 real retail-investor posts, labeled under a written annotation guideline.
- **Inter-annotator agreement:** a second person labels a subset independently. Their agreement (Cohen's kappa) shows how subjective the task is and what score is realistically achievable.
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
| Human agreement (kappa) | – | – | – | – |

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
| M1 | Bias definitions, annotation guideline, labeled dataset, agreement | ⏳ Planned |
| M2 | LLM bias analyzer, baseline, one-command eval, error analysis | ⏳ Planned |
| M3 | Decision journal, CSV trade import, behavioral metrics, Streamlit UI | ⏳ Planned |
| M4 | Semantic search over past decisions (RAG), Recall@5 | Post-MVP |
| M5 | Outcome tracking | Post-MVP |
| M6 | LangGraph re-implementation and comparison | Post-MVP |

## License

TBD. The dataset license depends on source data terms (see REQUIREMENTS.md, REQ-002).
