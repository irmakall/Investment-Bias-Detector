# Investment Bias Detector — Requirements

**Version:** 0.1 (draft) · **Date:** 2026-11-20 · **Status:** MVP scope agreed, open decisions listed in §9

## 1. Purpose

Investment Bias Detector is an investment decision journal. It records the reasoning behind each buy/sell decision, flags cognitive biases in that reasoning, and computes behavioral metrics from trade history. It has two goals:

1. Help the author understand her own investing behavior and improve financial literacy.
2. Serve as the main CV project for AI engineering internship applications. The core of the project is a hand-labeled dataset and a rigorous evaluation.

## 2. Guiding principles

| Principle | Meaning in practice |
| :--- | :--- |
| Numbers from code, words from the LLM | Every metric and number is computed in Python. The LLM only explains numbers it is given and never produces new ones. |
| No buy/sell advice | The app analyzes decisions. It never says what to buy, sell or hold. |
| Privacy | The public demo runs only on a fictional portfolio and sample notes. Real portfolio data never leaves the local machine or the private database. |
| Narrow and deep | The evaluation is deep and everything else stays simple. Fewer, finished features. |
| Visible agent loop | Hand-written function-calling loop, no agent framework, so every prompt sent to the model is fully controlled during eval. |

## 3. Milestones and MVP boundary

| Milestone | Content | In MVP |
| :--- | :--- | :--- |
| **M1** Dataset | Bias definitions, annotation guideline, pilot, labeled dataset, inter-annotator agreement, train/test split | ✅ |
| **M2** Classifier + eval | LLM bias analyzer, TF-IDF baseline, one-command eval harness, error analysis | ✅ |
| **M3** Journal + metrics | Decision notes saved to Supabase, CSV trade import, behavioral metrics, Streamlit UI, demo mode | ✅ |
| M4 RAG | Semantic search over past decisions, Recall@5 eval | ❌ Post-MVP |
| M5 Outcome tracking | Match decisions to price outcomes | ❌ Post-MVP |
| M6 LangGraph comparison | Same agent rebuilt in LangGraph, compared in README | ❌ Post-MVP |

**Why RAG is post-MVP:** retrieval over ~20–30 personal notes would make Recall@5 trivially high (top-5 of 20 is 25% of the corpus) and the metric meaningless. M3 builds up the corpus that M4 needs.

## 4. Bias taxonomy (initial, to be revised after the pilot)

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

### 4.2 Labeling rules

- Multi-label. Each item gets **1–2 bias labels**, or exactly `no_bias`.
- `no_bias` cannot co-occur with any other label.
- Missing counter-arguments alone is **not** evidence of `confirmation`.
- Overlap tie-break rules (for example `fomo` vs `herd`) are defined in the annotation guideline.

### 4.3 Behavior-measured biases (computed from trades, not classified)

Disposition effect, holding period, trade frequency. See REQ-023.

## 5. Functional requirements

Source key: **Desc** = project description · **Disc** = scoping discussion, 2026-11-20

### 5.1 M1 — Dataset

| ID | Requirement Name | User Story | Acceptance Criteria | MoSCoW | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-001** | Annotation guideline | **As an** annotator **I want** a written guideline **so that** two people label the same text the same way. | **Given** the guideline (`docs/annotation_guideline.md`, versioned) **then** every label in §4.1 has: a definition, inclusion and exclusion rules, ≥2 positive examples, ≥1 borderline/negative example. Tie-break rules exist for `fomo`/`herd` and `anchoring`/`loss_aversion`. | **Must** | Desc, Disc |
| **REQ-002** | License check before collection | **As the** author **I want** each data source's license recorded before use **so that** the dataset can legally be used and possibly published. | **Given** a candidate source **when** it is added **then** `data/SOURCES.md` records source, license/ToS link, whether redistribution is allowed and the date checked. No post is collected from a source without an entry. | **Must** | Desc, Disc |
| **REQ-003** | Source post collection | **As the** author **I want** 300–500 real investor posts **so that** the test set reflects real investor language. | **Given** collected posts **then** each record has `id`, `source`, `source_id`, `text`, `collected_at`. Duplicates (same normalized text) are removed. Only English posts are kept. Posts with fewer than 5 words are dropped. | **Must** | Desc |
| **REQ-004** | Pilot labeling | **As the** author **I want** to label 50 posts with a second annotator first **so that** guideline problems are found before full labeling. | **Given** 50 posts labeled by both annotators **when** the pilot report script runs **then** it outputs per-class counts and per-class Cohen's kappa. **Then** any class with kappa < 0.4 is redefined or merged, and any class projected to have < 20 examples in the full set is merged or dropped. The guideline version is bumped. | **Must** | Disc |
| **REQ-005** | Full labeling | **As the** author **I want** the full set labeled under one guideline version **so that** labels are consistent. | **Given** the final guideline **then** every post has labels following §4.2, and each record stores the `guideline_version`. A validation script rejects records that break §4.2 (0 or >2 bias labels, `no_bias` combined with others). | **Must** | Desc, Disc |
| **REQ-006** | Inter-annotator agreement | **As the** author **I want** agreement measured on a shared subset **so that** I know how subjective the task is and what score is realistically achievable. | **Given** ≥100 posts (pilot included) labeled independently by both annotators **then** per-class and mean Cohen's kappa are computed by code and reported in the README next to model scores. | **Must** | Desc |
| **REQ-007** | Fixed train/test split | **As the** author **I want** a fixed, stratified split **so that** the test set is never used for training or prompt design. | **Given** the labeled set **when** the split script runs with a fixed seed **then** ~70/30 train/test ID lists are saved and stratified by label. After the first eval run the test ID list is frozen (its hash is recorded). Few-shot examples in prompts come only from the train split. | **Must** | Disc |
| **REQ-008** | Synthetic data isolation | **As the** author **I want** synthetic data used only for training **so that** eval results are not inflated. | **Given** LLM-generated notes **then** they are tagged `source=synthetic`, generated only for rare classes and stored only in train. An automated check fails the eval run if any synthetic ID appears in a test set. | **Must** | Desc |
| **REQ-009** | Personal notes test set | **As the** author **I want** my own labeled notes as a separate test set **so that** I can measure performance on the real use case (domain shift). | **Given** ≥50 own notes labeled with the same guideline **then** eval reports scores on this set separately from the public-post test set. | **Should** | Desc, Disc |
| **REQ-010** | Dataset publication | **As the** author **I want** to publish the labeled dataset on Hugging Face **so that** others can reuse it. | **Given** REQ-002 shows redistribution is allowed **then** the dataset is published with a dataset card (sources, guideline, agreement scores, license). | **Could** | Desc |

### 5.2 M2 — Classifier and evaluation

| ID | Requirement Name | User Story | Acceptance Criteria | MoSCoW | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-011** | LLM bias analysis | **As a** user **I want** my note analyzed for biases **so that** I see blind spots in my reasoning. | **Given** a note text **when** analysis runs **then** the output validates against a Pydantic schema: `labels` (follows §4.2), and for each label an `evidence` span and a `rationale`, plus 1–3 `questions`. On invalid output the system retries once, then returns `{"error": ...}`. | **Must** | Desc |
| **REQ-012** | Evidence grounding check | **As the** author **I want** evidence spans verified in code **so that** the model cannot cite text that isn't in the note. | **Given** an analysis result **then** each `evidence` string is checked to be a substring of the input (case/whitespace-normalized). The ungrounded-evidence rate is reported in eval. | **Should** | Disc |
| **REQ-013** | Reflective questions, no advice | **As a** user **I want** thought-provoking questions **so that** I reconsider my decision without being told what to do. | **Given** generated questions **then** none recommend buying, selling or holding. A code check flags advice phrases and reports their count in eval (target 0). A manual review of 30 sampled outputs finds 0 recommendations. | **Must** | Desc |
| **REQ-014** | Hand-written agent loop | **As the** author **I want** a framework-free function-calling loop **so that** every step and prompt is visible and controllable. | **Given** the agent **then** it uses no agent framework, tools return `{"error": ...}` instead of raising, and the loop stops after a configured maximum number of iterations (default 5). | **Must** | Desc |
| **REQ-015** | Baseline classifier | **As the** author **I want** a classical ML baseline **so that** the LLM's added value is measured, not assumed. | **Given** the train split (+ synthetic) **then** a TF-IDF + one-vs-rest logistic regression model is trained with a fixed seed and evaluated on the same test set(s) as the LLM. | **Must** | Desc |
| **REQ-016** | One-command eval | **As the** author **I want** to run the full evaluation with one command **so that** results are reproducible and easy to update. | **Given** a clean clone with env vars set **when** the single documented eval command runs **then** it evaluates LLM and baseline on every test set and writes: per-class precision/recall/F1, macro-F1, per-class confusion matrices, cost per item (USD), latency per item (p50/p95), and a Markdown table pasted into the README. | **Must** | Desc |
| **REQ-017** | Run metadata | **As the** author **I want** every eval run to record its setup **so that** results can be traced and compared. | **Given** an eval run **then** its results file stores: model name/version, prompt hash, guideline version, test-split hash, seed, date and git commit. | **Must** | Disc |
| **REQ-018** | Error analysis | **As the** author **I want** misclassifications exported and categorized **so that** I understand why the model fails. | **Given** an eval run **then** a file lists every misclassified item with gold vs predicted labels. The README contains ≥20 categorized errors (for example ambiguous text, guideline gap, model error). | **Must** | Desc |
| **REQ-019** | LLM response cache | **As the** author **I want** LLM responses cached by (prompt hash, input) **so that** re-running eval doesn't repeat paid calls. | **Given** an unchanged prompt and input **when** eval re-runs **then** the cached response is used and no API call is made. A flag forces a fresh run. | **Should** | Disc |

### 5.3 M3 — Journal, metrics, UI

| ID | Requirement Name | User Story | Acceptance Criteria | MoSCoW | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-020** | Write decision note | **As a** user **I want** to write a short reason for each trade **so that** my reasoning is recorded at decision time. | **Given** the UI **when** I submit ticker, market, side, date and note text **then** the note is saved to Supabase, analysis runs (REQ-011) and the result is stored linked to the note. | **Must** | Desc |
| **REQ-021** | View analysis | **As a** user **I want** to see the analysis next to my note **so that** I can reflect on it. | **Given** a saved note **then** the UI shows the labels, evidence spans highlighted in the note, rationale and questions. | **Must** | Desc |
| **REQ-022** | CSV trade import | **As a** user **I want** to import trades from a CSV **so that** metrics can be computed without a broker integration. | **Given** a CSV matching §7.1 **when** imported **then** valid rows are saved and invalid rows are rejected with row number and reason. Re-importing the same file creates no duplicates. | **Must** | Disc |
| **REQ-023** | Behavioral metrics | **As a** user **I want** metrics computed from my trades **so that** I see patterns I can't see trade by trade. | **Given** imported trades **then** pandas code computes: holding period (median, realized winners vs losers), trades per month, and a disposition proxy (winner vs loser holding-period ratio). Results are computed per currency and never mix USD and TRY. Unit tests check every metric against a hand-calculated fixture. | **Must** | Desc, Disc |
| **REQ-024** | Metric explanation guard | **As the** author **I want** the LLM's metric explanations checked **so that** it cannot invent numbers. | **Given** an LLM explanation of a metrics dict **then** code extracts every number in the text and verifies it appears in the input dict. On failure the explanation is regenerated once, then numbers are shown without explanation. | **Should** | Desc |
| **REQ-025** | Sample size display | **As a** user **I want** every aggregate to show its n **so that** I don't over-trust small samples. | **Given** any aggregate metric **then** n is displayed. If n < 10 the metric is labeled "insufficient data". | **Must** | Disc |
| **REQ-026** | Demo mode | **As a** visitor **I want** a working demo **so that** I can try the app without real data. | **Given** demo mode **then** the app loads only a seeded fictional portfolio and sample notes. Demo mode cannot read the real data tables. | **Must** | Desc |

## 6. Non-functional requirements

| ID | Attribute | Metric / Constraint Specification | Target Metric / Value | MoSCoW | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NFR-001** | Reproducibility | Full eval runs from a clean clone using README instructions only. | 1 command. ≤15 min on MacBook M2 for ≤200 test items (cache cold). | **Must** | Desc |
| **NFR-002** | Determinism | Fixed seeds and LLM temperature 0. | Two consecutive baseline runs give identical metrics. LLM macro-F1 spread over 3 runs is reported. | **Must** | Disc |
| **NFR-003** | Cost | LLM spend per full eval run is logged. | ≤ $1 per full eval run, or within the provider's free tier. | **Should** | Desc |
| **NFR-004** | Latency | Single-note analysis time, end to end. | p95 ≤ 10 s | **Should** | Desc |
| **NFR-005** | Privacy | Real trades and notes are never committed or shown publicly. | Real-data files are in `.gitignore`. Secrets are only in env vars. A pre-commit check blocks `.env` and `data/private/`. | **Must** | Desc |
| **NFR-006** | No financial advice | No output recommends buying, selling or holding. | 0 flagged outputs in eval (REQ-013). A disclaimer is visible on every analysis screen. | **Must** | Desc |
| **NFR-007** | Numbers from code | Any number shown to the user comes from Python code. | 100% of displayed numbers trace back to computed values (REQ-024). | **Must** | Desc |
| **NFR-008** | Provider independence | All LLM calls go through one client interface. | Switching provider changes only one module plus config. | **Should** | Disc |
| **NFR-009** | Robustness | Tools never raise exceptions to the agent loop. | Every tool returns either a result or `{"error": str}`. The loop has a max-iteration limit. | **Must** | Desc |
| **NFR-010** | Observability | Every LLM call is logged. | The log stores prompt, response, token counts, latency and cost per call. | **Should** | Disc |
| **NFR-011** | Testability | Core logic has automated tests. | `pytest` covers metrics, schema validation and the split-leakage check. Tests pass in GitHub Actions on every push. | **Should** | Disc |
| **NFR-012** | Language | Repo, code, documentation and decision notes are in English. | 100% | **Must** | Desc |
| **NFR-013** | Data licensing | Each data source's license status is documented before use. | `data/SOURCES.md` has 1 entry per source (REQ-002). | **Must** | Desc |

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

`id, source (stocktwits | reddit | personal | synthetic), text, labels[], annotator, guideline_version, split (train | test)`

## 8. Out of scope for MVP (Won't, this version)

- RAG over past decisions and Recall@5 eval (M4)
- Outcome tracking with price data (M5)
- LangGraph re-implementation and comparison (M6)
- Midas export importer
- Full PGR/PLR disposition measure (needs daily price history)
- FastAPI + React front end
- Any buy/sell/hold recommendation (permanently out of scope)

## 9. Open decisions

| Decision | Blocks | Notes |
| :--- | :--- | :--- |
| Data source licenses (StockTwits, Reddit/WSB) | M1 collection, REQ-010 | Must be resolved first (REQ-002). If unusable, find alternative open datasets. |
| LLM provider | M2 | Gemini free tier is an option. NFR-008 keeps this swappable. |
| Final bias list | Full labeling | Decided after the pilot (REQ-004). |
| Size of second-annotator subset | REQ-006 | Minimum 100. Depends on the second annotator's availability. |
| Embedding model | M4 | Post-MVP. |
