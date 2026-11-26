"""Behavioral metrics from trades (REQ-023). Numbers come from code, never from the LLM.

Cost method: weighted average cost, the way Midas shows it for US stocks.
- Only buys change the average cost. Sells don't, and fees are left out.
- When a position is fully sold, the next buy starts a new average.
Holding period follows the same idea: the quantity-weighted average buy date of the open position.

Every metric is computed per currency, so USD and TRY are never mixed.
"""

from datetime import date

import pandas as pd


def realized_sells(trades: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Match each sell to its open position.

    Returns (sells, unmatched). `sells` has one row per sell with avg_cost, pnl, return_pct and holding_days.
    `unmatched` lists sells with no (or not enough) shares bought before them in the data,
    for example shares bought before the first imported trade. They are left out of the metrics.
    """
    rows, unmatched = [], []
    ordered = trades.sort_values(["date", "id"]) if "id" in trades else trades.sort_values("date", kind="stable")

    for (ticker, currency), group in ordered.groupby(["ticker", "currency"], sort=False):
        qty, avg_cost, avg_day = 0.0, 0.0, 0.0         # avg_day: average buy date as a day number
        for t in group.itertuples():
            day = date.fromisoformat(str(t.date)).toordinal()
            if t.side == "buy":
                total = qty + t.quantity
                avg_cost = (avg_cost * qty + t.price * t.quantity) / total
                avg_day = (avg_day * qty + day * t.quantity) / total
                qty = total
            elif t.quantity > qty + 1e-9:
                unmatched.append({"date": str(t.date), "ticker": ticker, "quantity": t.quantity, "held": qty})
            else:
                pnl = (t.price - avg_cost) * t.quantity
                rows.append({
                    "date": str(t.date), "ticker": ticker, "currency": currency, "quantity": t.quantity,
                    "sell_price": t.price, "avg_cost": round(avg_cost, 4), "pnl": round(pnl, 4),
                    "return_pct": round((t.price / avg_cost - 1) * 100, 2),
                    "holding_days": round(day - avg_day, 1),
                })
                qty -= t.quantity
                if qty < 1e-9:                          # position closed: next buy starts fresh
                    qty, avg_cost, avg_day = 0.0, 0.0, 0.0

    return pd.DataFrame(rows), unmatched


def _median(s: pd.Series) -> float | None:
    return None if s.empty else float(s.median())


def behavior_metrics(trades: pd.DataFrame) -> dict:
    """Per-currency metrics. Every value comes with its sample size n (REQ-025)."""
    if trades.empty:
        return {"by_currency": {}, "unmatched_sells": []}

    sells, unmatched = realized_sells(trades)
    out = {}
    for currency, cur_trades in trades.groupby("currency"):
        s = sells[sells["currency"] == currency] if not sells.empty else sells
        winners = s[s["pnl"] > 0] if not s.empty else s
        losers = s[s["pnl"] < 0] if not s.empty else s
        hold_w = _median(winners["holding_days"]) if not winners.empty else None
        hold_l = _median(losers["holding_days"]) if not losers.empty else None
        per_month = cur_trades["date"].astype(str).str[:7].value_counts().sort_index()

        out[currency] = {
            "n_trades": int(len(cur_trades)),
            "n_sells": int(len(s)),
            "n_winners": int(len(winners)),
            "n_losers": int(len(losers)),
            "median_hold_days_winners": hold_w,
            "median_hold_days_losers": hold_l,
            # Disposition proxy: > 1 means losers are held longer than winners
            "disposition_ratio": round(hold_l / hold_w, 2) if hold_w and hold_l is not None else None,
            "trades_per_month": {m: int(n) for m, n in per_month.items()},
            "mean_trades_per_month": round(float(per_month.mean()), 2),
        }
    return {"by_currency": out, "unmatched_sells": unmatched}
