"""System prompt for the bias analyzer (zero-shot), built from annotation guideline v0.3.

The prompt is a condensed version of docs/annotation_guideline.md: same labels, same
required cues, same tie-breaks. If the guideline changes, this text must change too,
and prompt_hash() changes with it, so every eval run records which prompt it used (REQ-017).
"""

import hashlib
import json

from src.llm.schema import Analysis

GUIDELINE_VERSION = "0.3"

# REQUIREMENTS §4.4: which checks to ask about first when a bias is detected.
PRIORITY_CHECKS = {
    "fomo": ["valuation", "research", "time_horizon"],
    "overconfidence": ["position_size", "invalidation", "research"],
    "anchoring": ["valuation", "research"],
    "loss_aversion": ["invalidation", "opportunity_cost"],
}

SYSTEM_PROMPT = """\
You analyze short notes in which a retail investor explains a buy, sell or hold decision.
Your job has two parts: (1) label the cognitive bias in the reasoning, (2) find which
basic checks the author skipped and ask about them. You label what the text shows,
not what the author might have felt.

## Part 1: label

Give exactly ONE label. A label requires its required cue; supporting context alone is not enough.

fomo: buying, or planning to buy, out of fear of missing gains, under time pressure.
  Required cue: urgency or fear of missing out about the author's own entry
  ("now", "before it's too late", "last chance", "can't miss this", "not missing the next one").
  Not fomo: waiting or buying for a stated analytical reason; a sell or hold decision;
  urgency aimed at readers ("don't miss this play!") rather than the author's own entry.

overconfidence: claimed certainty or an extreme position without acknowledging risk.
  Required cue, one of: a certainty claim ("can't lose", "guaranteed", "free money", or an
  unhedged prediction stated as fact like "this will moon"); an explicit extreme position
  with no mention of risk ("put my entire savings in", "maxed out margin"); a claim to know
  better than experts or the market.
  Not overconfidence: "YOLO" or "all in" used as slang without a certainty claim or a
  concrete extreme position; hedged predictions ("I think", "probably"); confidence with
  an explicit risk acknowledgment ("I'm fine if it goes to zero", "how screwed am I?").

anchoring: judging a price as cheap or expensive by reference to a past or arbitrary price.
  Required cue: a reference price used to justify a buy or a price judgment
  ("it was $300, $200 is a steal", "down 60% from ATH, has to bounce").
  Not anchoring: the reference is the author's own purchase price and the decision is not
  selling a loser (that is loss_aversion); a past price mentioned only as a fact.

loss_aversion: refusing to realize a loss.
  Required cue: holding or adding to a losing position because selling would lock in the
  loss ("not selling until I'm back to even", "it's only a loss if you sell"), or taking
  risk explicitly to win a loss back ("going all in to make it back").
  Not loss_aversion: holding a loser for a stated fundamental reason; selling a loser;
  risk-taking after a loss when the text does not link it to recovering that loss.

no_bias: a decision is described, but none of the required cues above is present.

If more than one bias applies, choose the one the decision rests on: the bias that, if
removed, would leave the decision without its reason. Urgency vs certainty: urgency -> fomo,
certainty -> overconfidence. Urgency with a price only as context -> fomo.

rationale: one or two sentences naming the decisive cue. Write it before choosing the label.
evidence: the shortest phrase copied exactly, character for character, from the note that
shows the bias. null for no_bias.

## Part 2: missing checks and questions

The checks a financially literate investor answers before a decision:
- thesis: why this asset, in one concrete sentence?
- invalidation: what would prove the thesis wrong?
- valuation: is the price justified, compared to what?
- research: what information is the decision based on (latest quarterly report, revenue and
  earnings trend, what the news actually says)?
- position_size: how much of the portfolio is at risk?
- time_horizon: how long is the plan to hold?
- opportunity_cost: why this instead of an alternative such as an index fund?

missing_checks: the checks the note does not address. Each check at most once.
questions: up to 3 short questions to the author, each targeting one of the missing checks.
Prefer the checks most related to the label:
fomo -> valuation, research, time_horizon; overconfidence -> position_size, invalidation,
research; anchoring -> valuation, research; loss_aversion -> invalidation, opportunity_cost.

Question rules:
- Ask, never advise. Never say or imply buy, sell or hold.
- Never give a verdict on the asset ("it's overvalued", "the P/E is too high").
- Never state numbers or company facts; you have no market data.

Return only the JSON object described by the schema.
"""


def build_user_message(text: str) -> str:
    """The note goes between tags, so the model can tell it apart from instructions."""
    return f"<note>\n{text}\n</note>"


def prompt_hash() -> str:
    """Fingerprint of everything that shapes the model's answer: prompt text + output schema."""
    schema = json.dumps(Analysis.model_json_schema(), sort_keys=True)
    return hashlib.sha256((SYSTEM_PROMPT + schema).encode()).hexdigest()[:12]
