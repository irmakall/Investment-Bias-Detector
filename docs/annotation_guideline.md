# Annotation Guideline

**Version:** 0.3 · **Date:** 2026-11-21 · **Status:** Single-label (one label per post)

This guideline tells annotators how to label investor posts for cognitive biases. Two annotators following it independently should reach the same labels. When they don't, either the post is truly ambiguous or this guideline needs a fix. The pilot exists to find out which.

---

## 1. What we are labeling

We label **what the text shows**, not what the author really felt.

> ❌ "Did this person actually feel FOMO?" (unknowable)
> ✅ "Does this text match our written definition of FOMO?" (answerable)

A label is "correct" when it follows this guideline.

## 2. Labeling procedure

For each post, go through these steps in order.

### Step 1: Is it about the author's own investment decision?

We only label posts that express the author's **own** buy, sell or hold decision, intention, or the reasoning behind it.

| Mark as `skip` when the post is… | Example (invented) |
| :--- | :--- |
| A question with no decision | "What do you guys think about AMD earnings?" |
| News or a fact with no personal decision | "TSLA deliveries beat estimates." |
| A meme, joke or reaction with no reasoning | "🚀🚀🚀", "this sub is a casino lol" |
| About someone else's decision only | "My uncle bought GME at the top." |
| Advice or promotion aimed at readers, with no clear decision of the author's own | "Why I keep telling you to buy shares. This may squeeze today." |
| Outcome only: a gain/loss report with no reasoning behind the decision | "First week after buying my first option ($3400 to $6000)" |
| Clearly sarcastic (for example ends with "/s", or the sarcasm is unmistakable) | "Yeah, buying more puts because stocks only go down /s" |
| Non-English, unreadable, or fewer than 5 words | — |
| Sexually explicit content or hate speech aimed at a group, even if it contains a decision (use `skip_reason = explicit`). Everyday profanity like "this stock is f***ed" and insults that are common WSB slang are labeled normally, but such posts are never quoted in the README. | — |

Record the reason in `skip_reason` using one of: `question`, `news`, `meme`, `other_person`, `no_decision`, `outcome_only`, `sarcasm`, `explicit`, `other`. Skipped posts are not part of the dataset.

**Comments with missing context:** a comment may refer to something we can't see ("that's why I sold my call yesterday"). Label only what the visible text shows. If the visible text has a decision but no cue, it is `no_bias`.

**Why skip instead of labeling `no_bias`?** WSB is full of memes and questions. If they all became `no_bias`, that class would be huge and trivially easy, and the test set would look nothing like the real use case (personal decision notes).

### Step 2: Check each bias

Go through the six biases in §4. A label requires its **required cue** (§4). Supporting cues alone are not enough.

### Step 3: Choose one label

- Give **exactly one** label: one bias or `no_bias`.
- If more than one bias seems to apply, choose the one **the decision rests on**: the bias that, if removed, would leave the decision without its reason. The others are context.
- When two labels overlap, use the tie-break rules in §5. If neither clearly dominates, use `unclear` (Step 5).

### Step 4: Record evidence

For the bias label, copy the **shortest phrase** from the post that triggered it into `evidence`. This makes disagreements easy to discuss and errors easy to analyze.

### Step 5: Unclear?

If the post is decision-related but you still can't decide after applying §4 and §5, set `status = unclear` and write why in `notes`. Unclear posts are excluded from the test set and counted in the README.

Do not agonize. **Aim for under 1 minute per post.** If it takes longer, it's probably `unclear`.

---

## 3. Label set

| Label | One-line test |
| :--- | :--- |
| `fomo` | Is the author rushing in because they fear missing gains? |
| `herd` | Is "others are doing it" the justification? |
| `overconfidence` | Does the author claim certainty or take an extreme position without acknowledging risk? |
| `anchoring` | Is a buy/sell price judged against a past or arbitrary price? |
| `loss_aversion` | Is the author refusing to accept a loss? |
| `confirmation` | Does the author explicitly dismiss or mock contrary information? |
| `no_bias` | Decision-related, but none of the above. |

---

## 4. Bias definitions

All examples are invented and written in the style of WSB posts.

### 4.1 `fomo` — Fear of missing out

**Definition:** Buying, or planning to buy, out of fear of missing gains that others are getting or that seem about to happen, under time pressure.

**Why it happens:** Regret aversion. Missing a gain can feel worse than losing money, so the fear of future regret overrides analysis (Loomes & Sugden, 1982).

**Required cue:** **Urgency or fear of missing out** about entering a position. For example "now", "before it's too late", "last chance", "can't miss this", "not missing the next one".

**Supporting cues:** the price has already risen sharply. Regret about a past missed opportunity. "Buy now, research later".

**Do NOT label when:**
- The price rose, but the author waits or buys for a stated analytical reason.
- The decision is a sell or a hold. FOMO is about getting in.
- The urgency is aimed at **readers** ("don't miss this play!") rather than the author's own entry. That is promotion, not the author's FOMO.

| | Example | Label |
| :--- | :--- | :--- |
| ✅ | "Already up 40% this week and I'm still on the sidelines. Buying at open, can't watch it run without me." | `fomo` |
| ✅ | "Missed NVDA last year. Not making that mistake again, loading up now." | `fomo` |
| ❌ | "Up 50%, I'll wait for a pullback before adding." | `no_bias` |

### 4.2 `herd` — Herd behavior

**Definition:** Justifying a decision by what other people are doing, rather than by one's own analysis.

**Why it happens:** People treat the crowd's actions as information ("they must know something"). This can lead to everyone copying everyone (Banerjee, 1992; Bikhchandani, Hirshleifer & Welch, 1992).

**Required cue:** **Other people's actions or opinions are given as a reason** for the decision. For example "everyone is buying", "WSB is all in", "my whole office bought", "they can't all be wrong".

**Do NOT label when:**
- Others are only mentioned, not used as a reason. "Saw a DD on WSB, checked the numbers myself, the margins look strong" → the reason is the author's own analysis.
- The author goes against the crowd.

| | Example | Label |
| :--- | :--- | :--- |
| ✅ | "Literally everyone here is loading PLTR calls, so I'm in too." | `herd` |
| ✅ | "My whole team bought TSLA, figured they can't all be wrong." | `herd` |
| ❌ | "Everyone's piling into this, which is exactly why I'm staying out." | `no_bias` |

### 4.3 `overconfidence`

**Definition:** Overestimating one's own knowledge or the certainty of an outcome, shown through certainty language or an extreme position taken without acknowledging risk.

**Why it happens:** People overrate their own information and skill. In the stock market this shows up as excessive trading and concentrated bets (Odean, 1998; Barber & Odean, 2001).

**Required cue:** **one** of:
- A certainty claim about the outcome: "can't lose", "guaranteed", "free money", "100% going up", "easiest trade ever". An **unhedged prediction stated as fact** also counts ("materials gonna rip tomorrow", "this will moon"). A hedged prediction does not ("I think", "I believe", "probably", "could").
- An explicitly extreme position with no mention of risk: "put my entire savings in", "maxed out margin", "took a loan to buy".
- A claim to know better than experts or the market: "analysts have the valuation massively wrong", "the market is completely mispricing this".

**Do NOT label when:**
- "YOLO" or "all in" is used as slang without a certainty claim or a concrete extreme position. These words are everywhere on WSB.
- The author is confident but acknowledges risk: "I'm fairly sure, but I sized it so I can lose it all."

| | Example | Label |
| :--- | :--- | :--- |
| ✅ | "This is literally free money, earnings are a guaranteed beat." | `overconfidence` |
| ✅ | "Put my entire emergency fund into 0DTE calls. Literally can't lose." | `overconfidence` |
| ❌ | "Bullish, but this is 5% of my portfolio. I'm fine if it goes to zero." | `no_bias` |

### 4.4 `anchoring`

**Definition:** Judging whether a price is cheap or expensive by reference to a past or arbitrary price, instead of the asset's current value.

**Why it happens:** People use the first number they see as a reference point and adjust too little from it (Tversky & Kahneman, 1974).

**Required cue:** A **reference price** used to justify a **buy** or price judgment. For example "it was $300, now $200 is a steal", "down 60% from ATH, has to bounce", "cheaper than when I first looked at it".

**Do NOT label when:**
- The reference price is the author's own **purchase price** and the decision is about not selling a loser → `loss_aversion` (see §5).
- A past price is only mentioned as a fact, with no "cheap/expensive" judgment.

| | Example | Label |
| :--- | :--- | :--- |
| ✅ | "It was $300 in January, buying at $180 is basically a discount." | `anchoring` |
| ✅ | "Down 70% from the all-time high, can't go much lower." | `anchoring` |
| ❌ | "Bought at $180. Revenue grew 30% YoY and it trades at 15x earnings." | `no_bias` |

### 4.5 `loss_aversion`

**Definition:** Refusing to realize a loss, or treating losses as much more painful than equivalent gains, which leads to holding losers.

**Why it happens:** Losses weigh roughly twice as much as equal gains (Kahneman & Tversky, 1979). After a loss, people often take extra risk to "get back to even" (Thaler & Johnson, 1990).

**Required cue:** The author **holds or adds to a losing position because selling would lock in the loss**. For example "not selling until I'm back to even", "it's not a loss until I sell", "averaging down so I can break even sooner".

**Do NOT label when:**
- The author holds a losing position for a stated fundamental reason. "Down 20%, but the thesis hasn't changed: contract renewals are on track."
- The author sells a loser. That is the opposite behavior.
- The author takes a big risk after a large loss, but the text does not link the risk to recovering that loss. Risk-taking after losses (the break-even effect) counts only when the text says so explicitly.

| | Example | Label |
| :--- | :--- | :--- |
| ✅ | "Down 35% but I'm not selling until I'm back to even." | `loss_aversion` |
| ✅ | "It's only a loss if you sell. Diamond hands." | `loss_aversion` |
| ❌ | "Down 30%, cut it. The thesis was wrong, moving on." | `no_bias` |
| ✅ | "Down 64% this year, going all in to make it back." | `loss_aversion` |
| ❌ | "Down 64% this year, all in on MVST with what's left." (no link to recovering the loss) | not `loss_aversion` |

### 4.6 `confirmation` — Confirmation bias (narrow definition)

**Definition:** Seeking or accepting only information that supports one's view while **explicitly dismissing, mocking or refusing to consider** contrary information.

**Why it happens:** People favor evidence that fits what they already believe (Nickerson, 1998).

**Required cue:** **Explicit dismissal of contrary information or people.** For example "bears are idiots", "ignore the FUD", "every negative article is paid shills", "not reading anything bearish".

**Important:** Short posts rarely include counter-arguments. **A missing counter-argument is NOT evidence.** Only label when contrary information is actively rejected.

| | Example | Label |
| :--- | :--- | :--- |
| ✅ | "Short report dropped, it's all FUD from hedgies. Bought more." | `confirmation` |
| ✅ | "Muted everyone bearish on this, they don't get it." | `confirmation` |
| ❌ | "Bullish on AMD, the new chips look great." (one-sided, nothing dismissed) | `no_bias` |

### 4.7 `no_bias`

**Definition:** A decision-related post (it passed Step 1) where no required cue from §4.1–4.6 is present.

| | Example | Label |
| :--- | :--- | :--- |
| ✅ | "Trimmed 20% of my MSFT position to rebalance, it grew past my 15% limit." | `no_bias` |
| ✅ | "Bought more after reading the 10-K: cloud margins improved for the third quarter in a row." | `no_bias` |

---

## 5. Tie-break rules

| Overlap | Rule | Example |
| :--- | :--- | :--- |
| `fomo` vs `herd` | **Others as the reason** → `herd`. **Urgency or fear of missing out** → `fomo`. Both present → the one the decision rests on. | "WSB is all in and it's up 80% today, I need in NOW" → `fomo` (the urgency drives the entry, the crowd is context) |
| `anchoring` vs `loss_aversion` | The reference is **the author's own buy price** and the decision is **not selling** → `loss_aversion`. The reference is **any past price** used to judge a **buy** as cheap → `anchoring`. | "Not selling below my $250 cost" → `loss_aversion`. "Was $300, $200 is cheap" → `anchoring` |
| `fomo` vs `overconfidence` | Urgency → `fomo`. Certainty → `overconfidence`. Both explicit → the one the decision rests on, otherwise `unclear`. | "Guaranteed 10-bagger, buying a few more" → `overconfidence` |
| `fomo` vs `anchoring` | If the main driver is urgency and the price is only context → `fomo` only. | "Last chance under $20 before earnings" → `fomo` |
| `overconfidence` with risk acknowledged | An extreme position plus an explicit risk acknowledgment ("how screwed am I?", "I'm fine if it goes to zero") → not `overconfidence`. | "Threw my last 2.4K into calls. How screwed am I?" → `no_bias` |

---

## 6. Model-assisted annotation

To keep the workload manageable, an LLM suggests labels and the annotator reviews them (REQ-005).

- The LLM fills in `status`, `labels`, `evidence` and `skip_reason`. The annotator reads every row and corrects these columns in place when needed, and writes any doubt in `notes` even if the label is not changed.
- Changes to the suggestions are not tracked: the final file does not keep the original suggestions. `suggested_by` records which model made them.
- **Anchoring check (optional):** the annotator labels a small subset **blind**, before seeing the suggestions. Agreement between the blind labels and the suggestions is reported in the README (REQ-006).
- The model that suggests labels must be different from the models evaluated in M2.

## 7. Output format

Labeling happens in a **working file** under `data/raw/` (git-ignored), because it holds post texts. One row per post:

| Column | Values |
| :--- | :--- |
| `id` | Reddit ID from the source dataset |
| `text`, `text_tr` | Post text and a reading aid translation |
| `status` | `labeled` / `skip` / `unclear` |
| `labels` | Exactly one label, for example `fomo`. Empty unless `status = labeled` |
| `evidence` | One phrase for the bias label. Empty for `no_bias` |
| `skip_reason` | Only when `status = skip` (see Step 1) |
| `notes` | Free text, optional |
| `suggested_by` | The model that suggested the labels (§6) |
| `annotator`, `guideline_version` | Who labeled, under which guideline version |

`python -m src.data.labels validate` checks every rule in this guideline that code can check.
`python -m src.data.labels export` writes `data/labels/<annotator>.csv` for git: IDs and labels only, **no text and no evidence**, and only when every row is valid.

---

## 8. Changelog

| Version | Date | Change |
| :--- | :--- | :--- |
| 0.1 | 2026-11-20 | First draft. Added `explicit` skip rule. |
| 0.2 | 2026-11-20 | After pilot review: `outcome_only` and `no_decision` skip reasons, missing-context rule, WSB insult rule, FOMO excludes urgency aimed at readers, new overconfidence cue (claims experts are wrong), risk-acknowledged tie-break, unhedged predictions count as certainty claims, break-even rule for loss aversion, model-assisted annotation section, working file vs exported file. |
| 0.2 | 2026-11-21 | Process only, labeling rules unchanged: `checked` and `suggested_*` columns removed, review changes are not tracked (§6, §7). |
| 0.3 | 2026-11-21 | Single-label: exactly one label per post, chosen by "the bias the decision rests on" (Step 3). Tie-break rules no longer give two labels (§5). The 14 two-label posts from v0.2 are re-labeled by hand under this rule. |

## References

- Banerjee, A. (1992). A simple model of herd behavior. *Quarterly Journal of Economics.*
- Barber, B. & Odean, T. (2001). Boys will be boys: Gender, overconfidence, and common stock investment. *Quarterly Journal of Economics.*
- Bikhchandani, S., Hirshleifer, D. & Welch, I. (1992). A theory of fads, fashion, custom, and cultural change as informational cascades. *Journal of Political Economy.*
- Kahneman, D. & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. *Econometrica.*
- Loomes, G. & Sugden, R. (1982). Regret theory. *Economic Journal.*
- Nickerson, R. (1998). Confirmation bias: A ubiquitous phenomenon in many guises. *Review of General Psychology.*
- Odean, T. (1998). Volatility, price, and profit when all traders are above average. *Journal of Finance.*
- Thaler, R. & Johnson, E. (1990). Gambling with the house money and trying to break even. *Management Science.*
- Tversky, A. & Kahneman, D. (1974). Judgment under uncertainty: Heuristics and biases. *Science.*
