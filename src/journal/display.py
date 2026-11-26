"""Small pure helpers for the UI, kept out of app.py so they can be unit-tested."""

import html
import re

LABEL_NAMES = {
    "fomo": "FOMO",
    "loss_aversion": "Loss aversion",
    "anchoring": "Anchoring",
    "overconfidence": "Overconfidence",
    "no_bias": "No clear bias",
}

CHECK_NAMES = {
    "thesis": "Thesis",
    "invalidation": "What would prove it wrong",
    "valuation": "Valuation",
    "research": "Research",
    "position_size": "Position size",
    "time_horizon": "Time horizon",
    "opportunity_cost": "Opportunity cost",
}


def highlight_evidence(text: str, evidence: str | None) -> str:
    """Return the note as safe HTML with the evidence phrase wrapped in <mark>.

    The match ignores case and extra spaces, like the grounding check in eval (REQ-012).
    Every piece of user text is escaped, so a note containing "<script>" is shown as text.
    """
    def safe(s: str) -> str:
        return html.escape(s).replace("\n", "<br>")

    if not evidence or not evidence.strip():
        return safe(text)
    pattern = r"\s+".join(re.escape(word) for word in evidence.split())
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return safe(text)
    s, e = match.span()
    return f"{safe(text[:s])}<mark>{safe(text[s:e])}</mark>{safe(text[e:])}"


MIN_N = 10   # REQ-025: below this, a metric is shown but labeled "insufficient data"


def with_n(value: str | None, n: int) -> str:
    """Every aggregate shows its sample size (REQ-025)."""
    if value is None or n == 0:
        return f"– (n={n})"
    note = " · insufficient data" if n < MIN_N else ""
    return f"{value} (n={n}){note}"
