# Annotation Guideline

**Version:** 0.1 · **Date:** 2026-11-20 · **Status:** Draft, to be revised after the 50-post pilot (REQ-004)

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
| Clearly sarcastic (for example ends with "/s", or the sarcasm is unmistakable) | "Yeah, buying more puts because stocks only go down /s" |
| Non-English, unreadable, or fewer than 5 words | — |

Record the reason in `skip_reason`. Skipped posts are not part of the dataset.

**Why skip instead of labeling `no_bias`?** WSB is full of memes and questions. If they all became `no_bias`, that class would be huge and trivially easy, and the test set would look nothing like the real use case (personal decision notes).

### Step 2: Check each bias

Go through the six biases in §4. A label requires its **required cue** (§4). Supporting cues alone are not enough.

### Step 3: Apply the multi-label rules

- Give **1 or 2** bias labels, or exactly `no_bias`.
- `no_bias` never appears together with another label.
- If 3 or more biases seem to apply, keep the 2 with the **most explicit** text evidence.
- When two labels overlap, use the tie-break rules in §5.

### Step 4: Record evidence

For each bias label, copy the **shortest phrase** from the post that triggered it into `evidence`. This makes disagreements easy to discuss and errors easy to analyze.

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
- A certainty claim about the outcome: "can't lose", "guaranteed", "free money", "100% going up", "easiest trade ever".
- An explicitly extreme position with no mention of risk: "put my entire savings in", "maxed out margin", "took a loan to buy".

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

| | Example | Label |
| :--- | :--- | :--- |
| ✅ | "Down 35% but I'm not selling until I'm back to even." | `loss_aversion` |
| ✅ | "It's only a loss if you sell. Diamond hands." | `loss_aversion` |
| ❌ | "Down 30%, cut it. The thesis was wrong, moving on." | `no_bias` |

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
| `fomo` vs `herd` | **Others as the reason** → `herd`. **Urgency or fear of missing out** → `fomo`. Both present → both labels. | "WSB is all in and it's up 80% today, I need in NOW" → `fomo` + `herd` |
| `anchoring` vs `loss_aversion` | The reference is **the author's own buy price** and the decision is **not selling** → `loss_aversion`. The reference is **any past price** used to judge a **buy** as cheap → `anchoring`. | "Not selling below my $250 cost" → `loss_aversion`. "Was $300, $200 is cheap" → `anchoring` |
| `fomo` vs `overconfidence` | Urgency → `fomo`. Certainty → `overconfidence`. Both explicit → both labels. | "Guaranteed 10-bagger, last chance to get in under $5" → both |
| `fomo` vs `anchoring` | If the main driver is urgency and the price is only context → `fomo` only. | "Last chance under $20 before earnings" → `fomo` |

---

## 6. Output format

One row per post, in `data/labels/<annotator>.csv`:

| Column | Values |
| :--- | :--- |
| `id` | Reddit ID from the source dataset |
| `status` | `labeled` / `skip` / `unclear` |
| `labels` | Pipe-separated, for example `fomo\|herd`. Empty unless `status = labeled` |
| `evidence` | One phrase per label, pipe-separated in the same order |
| `skip_reason` | Only when `status = skip` |
| `notes` | Free text, optional |
| `annotator` | Annotator ID |
| `guideline_version` | For example `0.1` |

---

## 7. Changelog

| Version | Date | Change |
| :--- | :--- | :--- |
| 0.1 | 2026-11-20 | First draft |

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
