# Investment Bias Detector — Requirements

**Version:** 0.4 · **Date:** 2026-11-26 · **Status:** MVP scope agreed, open decisions listed in §9

**Changelog:** 0.4 — M3.5 guided reflection added (§5.4): curated how-to guides per check, answers to the questions, LLM check of whether an answer covers its check, the bias label stays unchanged, and a proceed/change/cancel outcome after reflecting. Planned after M3 and the M2 error analysis. 0.3 — `research` check added to the financial literacy checklist (§4.4) after reviewing the first own note; REQ-007 split implemented; REQ-005 simplified: reviewer changes to suggestions are no longer tracked (no `checked` or `suggested_*` columns); the dataset is now single-label (§4.2), so every item has exactly one label; classification is one structured LLM call, and the hand-written agent loop (REQ-014) moves to M4, where a tool is actually needed; scope cut to the core: Should/Could items removed, REQ-012 and REQ-019 raised to Must, own notes (REQ-009) moved to post-MVP; synthetic data (REQ-008) cut; storage is SQLite until M4. 0.2 — financial literacy checklist (§4.4) with checklist-targeted questions (REQ-027), question quality eval (REQ-028) and checklist coverage over time (REQ-029); 4 evaluated biases after the pilot; stratified sampling; model-assisted labeling with a single reviewer; requirements rewritten as requirement + done-when.

## 1. Purpose

Investment Bias Detector is an investment decision journal. It records the reasoning behind each buy/sell decision, flags cognitive biases in that reasoning, and computes behavioral metrics from trade history. It has two goals:

1. Help the author understand her own investing behavior and improve financial literacy. Beyond classifying biases, the app pushes the author toward the checks a financially literate investor makes before deciding (§4.4).
2. Serve as the main CV project for AI engineering internship applications. The core of the project is a human-reviewed labeled dataset and a rigorous evaluation.

## 2. Guiding principles

| Principle | Meaning in practice |
| :--- | :--- |
| Numbers from code, words from the LLM | Every metric and number is computed in Python. The LLM only explains numbers it is given and never produces new ones. |
| No buy/sell advice | The app analyzes decisions. It never says what to buy, sell or hold. |
| Ask, don't judge | Questions point to what the author didn't check. They never state a verdict on the stock (for example "the P/E is too high"). |
| Privacy | The public demo runs only on a fictional portfolio and sample notes. Real portfolio data never leaves the local machine: notes and trades live in a local SQLite file under the git-ignored `data/private/`. Only the note text is sent to the LLM (Gemini free tier, see §9), so notes contain no personal or account details. |
| Narrow and deep | The evaluation is deep and everything else stays simple. Fewer, finished features. |
| Visible LLM calls | No agent framework, so every prompt sent to the model is fully controlled during eval. Classification is a single structured call: the model has everything it needs in the prompt, so a tool loop would only add calls, cost and variance. The hand-written agent loop comes in M4, where the model must decide when to search past decisions. |

## 3. Milestones and MVP boundary

| Milestone | Content | In MVP |
| :--- | :--- | :--- |
| **M1** Dataset | Bias definitions, annotation guideline, pilot, model-assisted labeled dataset, train/test split | ✅ |
| **M2** Classifier + eval | LLM bias analyzer, checklist-targeted questions, TF-IDF baseline, one-command eval harness, error analysis | ✅ |
| **M3** Journal + metrics | Decision notes saved to a local SQLite file, CSV trade import, behavioral metrics, Streamlit UI, demo mode | ✅ |
| M3.5 Guided reflection | Hints and how-to guides for each missing check, answering the questions, checks ticked when an answer covers them, proceed/change/cancel after reflecting | ⏳ Planned, after M3 and REQ-018 |
| M4 RAG | Semantic search over past decisions as a tool in a hand-written agent loop (REQ-014), storage moved to Supabase + pgvector, Recall@5 eval | ❌ Post-MVP |
| M5 Outcome tracking | Match decisions to price outcomes | ❌ Post-MVP |
| M6 LangGraph comparison | Same agent rebuilt in LangGraph, compared in README | ❌ Post-MVP |

**Why RAG is post-MVP:** retrieval over ~20–30 personal notes would make Recall@5 trivially high (top-5 of 20 is 25% of the corpus) and the metric meaningless. M3 builds up the corpus that M4 needs.

## 4. Bias taxonomy (revised after the pilot, 2026-11-20)

### 4.1 Text-detectable biases (classifier labels)

| Label | Working definition | Typical cue | Known overlap |
| :--- | :--- | :--- | :--- |
| `fomo` | Acting out of fear of missing gains, under time pressure | "before it's too late", "can't miss this" | `herd` |
| `herd` | Justifying the decision by what others are doing | "everyone is buying", "WSB is all in" | `fomo` |
| `overconfidence` | Certainty language or outsized position without acknowledging risk | "can't lose", "guaranteed", "all in" | — |
| `anchoring` | Judging value by reference to a past or arbitrary price | "it was $300, $200 is cheap" | `loss_aversion` |
| `loss_aversion` | Refusing to realize a loss, waiting to break even | "I'll sell when it's back to my buy price" | `anchoring` |
| `confirmation` | **Narrow definition:** explicitly dismissing or mocking contrary information | "bears are idiots", "ignore the FUD" | — |
| `no_bias` | No identifiable bias in the text | — | Exclusive with all others |

**Evaluated labels (MVP):** `overconfidence`, `anchoring`, `loss_aversion`, `fomo`, `no_bias`.

`herd` and `confirmation` stay in the annotation guideline, so the information is not lost, but they are **not evaluated and not shown in the app** in the MVP. The pilot found 0 and 1 examples of them out of 26 labeled WSB posts, so even targeted sampling is unlikely to reach the 20-example minimum (REQ-004).

### 4.2 Labeling rules

- Single-label. Each item gets **exactly one** label: one bias or `no_bias`.
- When several biases appear, the label is the bias the decision rests on. If none clearly dominates, the item is `unclear`.
- Why single-label: with ~280 labeled items, only 14 had two labels, too few to learn label combinations. One label per item keeps the split, the baseline, the metrics and the LLM output simple.
- Missing counter-arguments alone is **not** evidence of `confirmation`.
- Overlap tie-break rules (for example `fomo` vs `herd`) are defined in the annotation guideline.

### 4.3 Behavior-measured biases (computed from trades, not classified)

Disposition effect, holding period, trade frequency. See REQ-023.

### 4.4 Financial literacy checklist

The checks a financially literate investor answers before a decision. The checklist is separate from the bias labels: biases describe what went wrong in the reasoning, checks describe what was left out. It is used only for question generation (REQ-027), not for the M1 dataset labels.

| Check ID | What a literate investor asks | Example question to the author |
| :--- | :--- | :--- |
| `thesis` | Why this asset, in one concrete sentence? | "What is the one-sentence reason you're buying this?" |
| `invalidation` | What would prove the thesis wrong? | "What would have to happen for you to admit the thesis was wrong?" |
| `valuation` | Is the price justified, compared to what? | "How did you decide this price is reasonable? What did you compare it to?" |
| `research` | What information is the decision based on: the latest quarterly report, the revenue and earnings trend, what the news actually says? | "Did you look at the latest quarterly report? Is revenue growing or shrinking?" |
| `position_size` | How much of the portfolio is at risk? | "This position is {position_pct}% of your portfolio. What happens to the total if it drops 50%?" |
| `time_horizon` | How long is the plan to hold? | "Are you planning to hold this for a week or for three years?" |
| `opportunity_cost` | Why this instead of the alternative (for example an index fund)? | "Why this stock rather than putting the same money in an index fund?" |

Bias → priority checks (which checks to ask about first when a bias is detected):

| Bias | Priority checks | Why |
| :--- | :--- | :--- |
| `fomo` | `valuation`, `research`, `time_horizon` | Urgency replaces price analysis, research and a holding plan ("buy now, research later"). |
| `herd` | `thesis`, `opportunity_cost` | Others' actions replace an own reason. |
| `overconfidence` | `position_size`, `invalidation`, `research` | Certainty hides downside and sizing risk, and often rests on no stated evidence. |
| `anchoring` | `valuation`, `research` | A past price replaces a current value judgment and a look at the business itself. ("Would you buy it today at this price from scratch?") |
| `loss_aversion` | `invalidation`, `opportunity_cost` | Waiting to break even ignores whether the thesis still holds and where the money could be instead. |
| `confirmation` | `invalidation` | Dismissing contrary info means no exit condition was considered. |
| `no_bias` | Any missing check | Even an unbiased note can skip checks. |

The app cannot know whether the author actually read a report. It only sees whether the note mentions any research, so `research` is always asked as a question. The LLM never states company figures itself (for example "revenue fell 10%"), in line with "numbers from code".

## 5. Functional requirements

**Status:** ✅ done · 🔄 in progress · ⏳ not started

### 5.1 M1 — Dataset

| ID | Requirement | Done when | Priority | Status |
| :--- | :--- | :--- | :--- | :---: |
| **REQ-001** | A written annotation guideline defines every label. | `docs/annotation_guideline.md` is versioned. Each label has a definition, a required cue, exclusions, ≥2 positive and ≥1 negative example. Overlapping pairs have tie-break rules. | Must | ✅ |
| **REQ-002** | Every data source is checked for license and platform terms before use. | `data/SOURCES.md` lists, per source: dataset license, platform terms, whether stable post IDs exist, status (`approved` / `pending` / `rejected`) and the date checked. Posts are sampled only from `approved` sources. | Must | ✅ |
| **REQ-003** | Posts are sampled from existing public datasets, with extra samples for rare biases. | No scraping and no API collection. Texts pass the filters (≥5 words, ≤1500 characters, no bots, no repeated texts, decision pre-filter). Sampling uses a general stratum plus one keyword stratum each for `fomo`, `loss_aversion`, `anchoring`, and a top-up sample from keyword strata only (`overconfidence`, `loss_aversion`, `anchoring`) for classes that stayed below 20. Each record has `id`, `source_type`, `stratum`, `text`. Pilot IDs are excluded. The same seed gives the same file. | Must | ✅ |
| **REQ-004** | A 50-post pilot tests the guideline before full labeling. | 50 posts are reviewed, per-class counts are computed, disagreements are turned into guideline rules, classes projected to have < 20 examples are merged, dropped or oversampled, and the guideline version is bumped. | Must | ✅ |
| **REQ-005** | Labels are suggested by an LLM and reviewed by a human. | The LLM fills in the label columns, the reviewer reads every row and corrects it in place when needed. Changes are not tracked separately, and the README states this. Final labels follow §4.2. Every row has `guideline_version` and `suggested_by`. The suggesting model is not one of the models evaluated in M2. A validation script rejects invalid records. | Must | ✅ |
| **REQ-007** | The labeled set has a fixed train/test split. | ~70/30 stratified split with a fixed seed, saved as ID lists. The test list is frozen after the first eval run (hash recorded). Few-shot examples come only from train. | Must | ✅ |

### 5.2 M2 — Classifier and evaluation

| ID | Requirement | Done when | Priority | Status |
| :--- | :--- | :--- | :--- | :---: |
| **REQ-011** | The LLM analyzes a note for biases and missing checks. | One structured call, no tool loop. Output validates against a Pydantic schema (§7.3): one label (§4.2), an evidence span and a rationale, `missing_checks` (§4.4 IDs), and 0–3 questions, each with `text` and `check`. Invalid output is retried once, then `{"error": ...}` is returned. | Must | ✅ |
| **REQ-012** | Evidence spans are verified in code. | Each evidence string is a substring of the input (case/whitespace-normalized). The ungrounded-evidence rate is reported in eval. | Must | ✅ |
| **REQ-013** | Reflective questions never give advice or a verdict. | No question recommends buying, selling or holding, or states a verdict on the asset ("it's overvalued"). A code check flags advice phrases and the eval count is 0. A manual review of 30 outputs finds 0. | Must | 🔄 |
| **REQ-015** | A classical ML baseline is evaluated next to the LLM. | TF-IDF + multiclass logistic regression, trained on train with a fixed seed, evaluated on the same test set. | Must | ✅ |
| **REQ-016** | The full evaluation runs with one command. | One documented command evaluates LLM and baseline on every test set and writes per-class P/R/F1, macro-F1, confusion matrices, cost per item, latency p50/p95, and a Markdown table for the README. | Must | ✅ |
| **REQ-017** | Every eval run records its setup. | The results file stores model name/version, prompt hash, guideline version, test-split hash, seed, date and git commit. | Must | ✅ |
| **REQ-018** | Errors are exported and analyzed. | A file lists every misclassified item with gold vs predicted label. The README has ≥20 categorized errors. README examples have no usernames or links and are ≤280 characters. | Must | 🔄 |
| **REQ-019** | LLM responses are cached. | An unchanged prompt and input reuse the cached response with no API call. A flag forces a fresh run. | Must | ✅ |
| **REQ-027** | Questions target the checks the note skipped. | Every question's `check` is in `missing_checks`. When a bias is detected and one of its priority checks (§4.4) is missing, at least one question targets it. If no check is missing, no question is asked. Numbers in questions (for example `position_pct`) are filled in by code from trade data. Without linked trade data, no question contains a number. | Must | 🔄 |

### 5.3 M3 — Journal, metrics, UI

| ID | Requirement | Done when | Priority | Status |
| :--- | :--- | :--- | :--- | :---: |
| **REQ-020** | I can write a decision note. | Submitting ticker, market, side, date and note saves it to the local SQLite database (`data/private/journal.db`), runs the analysis (REQ-011) and stores the result linked to the note. | Must | ✅ |
| **REQ-021** | I can see the analysis next to the note. | The UI shows the label, evidence highlighted in the note, rationale, missing checks and questions. | Must | ✅ |
| **REQ-022** | Trades are imported from a CSV. | Files matching §7.1 are imported. Invalid rows are rejected with row number and reason. Re-importing the same file creates no duplicates. | Must | ✅ |
| **REQ-023** | Behavioral metrics are computed from trades. | pandas computes median holding period (winners vs losers), trades per month and a disposition proxy, per currency, never mixing USD and TRY. Unit tests match a hand-calculated fixture. | Must | ✅ |
| **REQ-025** | Every aggregate shows its sample size. | n is displayed. If n < 10 the metric is labeled "insufficient data". | Must | ✅ |
| **REQ-026** | A public demo runs on fictional data. | Demo mode loads only a seeded fictional portfolio and sample notes, and never opens `data/private/`. | Must | 🔄 |

### 5.4 M3.5 — Guided reflection

**Why:** asking a question assumes the author knows how to answer it. "How did you decide this price is reasonable?" means little to someone who has never looked at a P/E ratio. This milestone turns the questions into a short learning loop and serves the first goal of the project (§1): financial literacy, not only bias detection.

**Flow:** note → analysis (label, missing checks, questions) → for each question a one-line hint and a step-by-step guide → the author answers → the LLM checks whether each answer covers its check → covered checks are ticked → the author records what they will do.

**Design rules:**

- **Guides are written by hand, not generated.** Each check in §4.4 has one short, reviewed guide. Code picks the guide from the question's `check`; the LLM is not involved. Reason: a generated guide can invent where to find data or state figures and verdicts ("the P/E is 40, too high"), which breaks "numbers from code" and "ask, don't judge".
- **The bias label never changes.** The label records the reasoning at decision time. A good answer afterwards does not undo the impulse, and changing the label would break metrics such as "3 of your 4 FOMO buys lost money".
- **A tick needs proof.** An answer covers a check only if it contains something concrete for that check (for `valuation`: a comparison with the company's own history or with peers). "I looked, it's fine" does not count. The LLM must quote the part of the answer that covers the check, and code verifies the quote, as in REQ-012.
- **No free chat in this milestone.** Free chat drifts toward advice ("so should I sell?") and cannot be evaluated. Open questions about the guides ("what is P/E?") belong to M4, where retrieval can be limited to the author's own guides.

| ID | Requirement | Done when | Priority | Status |
| :--- | :--- | :--- | :--- | :---: |
| **REQ-030** | Every check has a hint and a how-to guide. | `docs/guides/<check>.md` exists for all 7 checks in §4.4. Each has a one-line hint, what the concept is in plain words, where to find the data, how to compare (at least one concrete method), common mistakes, and an example answer pattern. ≤250 words each. Guides contain no figures about specific companies. | Must | ⏳ |
| **REQ-031** | The UI shows help under each question. | Under each question the hint is visible and the guide opens on demand. The guide is chosen by the question's `check` in code. | Must | ⏳ |
| **REQ-032** | I can answer the questions. | Each question has an answer field. Answers are saved in SQLite, linked to the analysis and the question. Saving answers never changes the stored analysis or its label. | Must | ⏳ |
| **REQ-033** | Answers are checked against their checks. | One structured call per submission. For each answer: `covered` (true/false), a quote from the answer when covered, and a follow-up question when not. The output validates against a Pydantic schema, and every quote is a substring of the answer (verified in code). The prompt and the original note are recorded like REQ-017. | Must | ⏳ |
| **REQ-034** | Covered checks are shown as ticked. | The UI shows `checks covered: k / n`, with each covered check ticked and its quote shown. Checks not covered show the follow-up question. | Must | ⏳ |
| **REQ-035** | I record what I will do after reflecting. | After answering, I choose proceed / change / cancel, saved with a timestamp. The metrics tab shows the share of decisions changed or cancelled, with n (REQ-025). | Must | ⏳ |
| **REQ-036** | The answer check is evaluated. | ≥30 hand-labeled (check, answer, covered) pairs, covering every check with both covered and not-covered examples. Precision and recall of `covered` are reported. Pairs are written by me, not taken from source datasets. | Must | ⏳ |

### 5.5 Post-MVP

| ID | Requirement | Done when | Priority | Status |
| :--- | :--- | :--- | :--- | :---: |
| **REQ-009** | My own decision notes form a separate test set. | ≥50 notes written at decision time are labeled with the same guideline. Their scores are reported separately. | Post-MVP | ⏳ |
| **REQ-014** | The RAG agent loop is hand-written. | No agent framework. The model gets a `search_past_decisions` tool and decides when to call it. Tools return `{"error": ...}` instead of raising. The loop stops after a max number of iterations (default 5). | Post-MVP (M4) | ⏳ |

## 6. Non-functional requirements

| ID | Requirement | Done when | Priority | Status |
| :--- | :--- | :--- | :--- | :---: |
| **NFR-001** | Eval is reproducible from a clean clone. | 1 command, ≤15 min on a MacBook M2 for ≤200 test items (cache cold). | Must | ✅ |
| **NFR-002** | Runs are deterministic. | Fixed seeds and LLM temperature 0. Two baseline runs give identical metrics. LLM macro-F1 spread over 3 runs is reported. | Must | ⏳ |
| **NFR-005** | Real data stays private. | Real-data files are git-ignored, secrets are only in env vars, and a pre-commit check blocks `.env` and `data/private/`. | Must | 🔄 |
| **NFR-006** | The app never gives financial advice. | 0 flagged outputs in eval (REQ-013) and a disclaimer on every analysis screen. | Must | ⏳ |
| **NFR-007** | Numbers come from code. | 100% of displayed numbers trace back to computed values (REQ-027). | Must | ⏳ |
| **NFR-008** | The LLM provider can be swapped. | Switching provider changes one module plus config. | Should | ✅ |
| **NFR-009** | LLM calls are robust. | Every LLM call and tool returns a result or `{"error": str}`. The M4 agent loop has a max-iteration limit. | Must | ⏳ |
| **NFR-011** | Core logic is tested. | `pytest` covers metrics, schema validation and the split-leakage check, and passes in GitHub Actions on every push. | Must | 🔄 |
| **NFR-012** | The project is in English. | Repo, code, documentation and decision notes are in English. | Must | 🔄 |
| **NFR-013** | Data licensing rules are followed. | `data/SOURCES.md` has one entry per source, 0 items are scraped, and 0 source texts appear in published files. | Must | 🔄 |

## 7. Data schemas

### 7.1 Trade CSV

| Column | Type | Rule |
| :--- | :--- | :--- |
| `date` | ISO date | Required |
| `ticker` | string | Required, uppercase |
| `market` | `US` \| `BIST` | Required |
| `side` | `buy` \| `sell` | Required |
| `quantity` | decimal > 0 | Required |
| `price` | decimal > 0 | Required, in `currency` |
| `currency` | `USD` \| `TRY` | Required |
| `fee` | decimal ≥ 0 | Optional, default 0 |
| `note_id` | string | Optional, links to a decision note |

A future Midas importer is an adapter that converts Midas exports into this schema. Metric code does not change.

### 7.2 Labeled item

`id, source (reddit | personal), text, label, annotator, guideline_version, split (train | test)`

### 7.3 Analysis result

`note_id, label, evidence{span, rationale}, missing_checks[], questions[{text, check}], model, prompt_hash, created_at`

## 8. Out of scope for MVP (Won't, this version)

- RAG over past decisions and Recall@5 eval (M4)
- Outcome tracking with price data (M5)
- LangGraph re-implementation and comparison (M6)
- Midas export importer
- Full PGR/PLR disposition measure (needs daily price history)
- A labeled gold set for `missing_checks` with F1 scoring (the REQ-013 manual review of 30 outputs is used instead)
- FastAPI + React front end
- Own decision notes as a separate test set (REQ-009, post-MVP): notes keep being written at decision time, the project does not wait for 50 of them
- Synthetic training data (former REQ-008): `class_weight="balanced"` already handles the class imbalance, and generated text would add a leakage risk for little gain
- Blind self-check of suggestion influence, Hugging Face publication of the labels, a question quality rubric, LLM explanations of metrics, checklist coverage over time (cut on 2026-11-21 to keep the MVP small)
- Any buy/sell/hold recommendation (permanently out of scope)

## 9. Open decisions

| Decision | Blocks | Notes |
| :--- | :--- | :--- |
| When reflection is used | M3.5 | Before the trade (decision can still change, proceed/change/cancel is meaningful) or after it (learning only). Proceed/change/cancel only makes sense before. |
| Follow-up rounds | REQ-033 | Start with one round (answer, check, done). Add a second round only if real use shows it is needed. |
| Who writes the guides | REQ-030 | Plan: I write them as part of studying, Claude reviews for accuracy and plain language. |
| Final checklist | REQ-027 | §4.4 is a draft. v0.3 added `research` after the first own note (AVGO). Revisit after ~10 own notes. |
| Embedding model | M4 | Post-MVP. |
| Identical same-day trades | REQ-022 | A trade's fingerprint is built from its fields, so two real trades with the same date, ticker, side, quantity, price and fee are imported as one. A unique trade ID column (for example a Midas order number) would fix this. Accepted as a known limitation for now. |

### Decided

| Decision | Date | Choice and why |
| :--- | :--- | :--- |
| LLM provider | 2026-11-21 | **Gemini (Flash models)** for M2. Known API from Briefly, free tier is enough for ~82 test items. Not Claude, because Claude suggested the labels (REQ-005). The free tier is used for both the WSB posts and my own notes. Free-tier inputs may be used to improve Google's products and may be read by human reviewers, so notes never contain personal or account details (name, broker account, portfolio value, income), and numbers such as position size are filled in by code and never sent to the model (REQ-027). The exact model ID is recorded per eval run (REQ-017), because Gemini model names change often. NFR-008 keeps a second provider possible. |
| Cost method | 2026-11-26 | **Weighted average cost, as Midas shows it.** Only buys change the average, sells and fees don't, and a fully sold position starts fresh. Holding period uses the quantity-weighted average buy date, the same idea applied to time. Matching Midas means the numbers agree with what I see in the app. Sells with no earlier buy in the data are reported as unmatched and left out of the metrics. The disposition proxy is median holding days of losers divided by winners (> 1: losers held longer). |
| Storage | 2026-11-21 | **SQLite** (Python standard library) for the MVP, in the git-ignored `data/private/`. A single-user journal needs no cloud database, real notes stay on the local machine, and the public demo needs no keys or separate tables. Supabase (Postgres + pgvector) comes with M4, where vector search is actually needed; the tables are plain SQL, so the move is small. |

## 10. Licensing and data-use policy

Three different things have separate rules. They should not be confused:

| What | Who owns it | Our rule |
| :--- | :--- | :--- |
| **Post texts** (Reddit, StockTwits) | The users who wrote them. Platform terms apply. | Used only for non-commercial evaluation and training inside this repo. Sampled from existing public datasets, never scraped. Never redistributed in bulk. Stored under `data/raw/`, which is git-ignored. |
| **Our labels, guideline, eval code** | The author | Labels and guideline: CC-BY-4.0. Code: MIT. |
| **Third-party dataset packaging** | The uploader (for example SocialGrep) | Follow the uploader's license, for example attribution for CC-BY-4.0. This license does not grant rights the uploader doesn't own. |

Platform terms checked on 2026-11-20:

- **Reddit:** user content is owned by its authors. The Data API terms (section 2.4) restrict machine-learning use without user permission. → No API collection. No redistribution of texts.
- **StockTwits:** the terms (revised 2026-07-10, section 5) prohibit automated extraction without written permission and grant no right to redistribute content in bulk. → No scraping. No redistribution of texts.

This is a good-faith reading of public terms, not legal advice.
