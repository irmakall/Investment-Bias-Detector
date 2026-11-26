"""Expected values are calculated by hand from tests/fixtures/trades_metrics.csv:

AVGO  buy 2 @100 (Jan 1), buy 2 @80 (Jan 11)  -> avg cost 90, avg buy date Jan 6
      sell 2 @120 (Jan 21) -> pnl +60, held 15 days  (winner)
      sell 2 @70  (Feb 5)  -> pnl -40, held 30 days  (loser)
TSLA  buy 1 @200 (Mar 1), sell 1 @220 (Mar 4) -> pnl +20, held 3 days (winner)
THYAO buy 10 @300 TRY (Mar 1), sell 10 @270 (Mar 11) -> pnl -300 TRY, held 10 days (loser)
NVDA  sell with no earlier buy -> unmatched
"""

from pathlib import Path

import pandas as pd
import pytest

from src.journal import db
from src.journal.importer import import_trades
from src.journal.metrics import behavior_metrics, realized_sells

FIXTURE = Path(__file__).parent / "fixtures" / "trades_metrics.csv"


@pytest.fixture
def trades():
    conn = db.connect(":memory:")
    import_trades(conn, FIXTURE)
    return pd.DataFrame(db.list_trades(conn))


def test_average_cost_like_midas(trades):
    sells, _ = realized_sells(trades)
    avgo = sells[sells["ticker"] == "AVGO"]
    assert list(avgo["avg_cost"]) == [90, 90]          # the first sell does not change the average
    assert list(avgo["pnl"]) == [60, -40]              # fees are not part of the cost
    assert list(avgo["holding_days"]) == [15, 30]


def test_sell_without_buy_is_unmatched(trades):
    _, unmatched = realized_sells(trades)
    assert [u["ticker"] for u in unmatched] == ["NVDA"]


def test_position_restarts_after_full_sell():
    t = pd.DataFrame([
        {"id": 1, "date": "2026-01-01", "ticker": "X", "currency": "USD", "side": "buy", "quantity": 1, "price": 10},
        {"id": 2, "date": "2026-01-02", "ticker": "X", "currency": "USD", "side": "sell", "quantity": 1, "price": 12},
        {"id": 3, "date": "2026-02-01", "ticker": "X", "currency": "USD", "side": "buy", "quantity": 1, "price": 50},
        {"id": 4, "date": "2026-02-03", "ticker": "X", "currency": "USD", "side": "sell", "quantity": 1, "price": 40},
    ])
    sells, _ = realized_sells(t)
    assert list(sells["avg_cost"]) == [10, 50]
    assert list(sells["holding_days"]) == [1, 2]


def test_metrics_per_currency(trades):
    m = behavior_metrics(trades)["by_currency"]
    usd, tl = m["USD"], m["TRY"]
    assert (usd["n_winners"], usd["n_losers"]) == (2, 1)
    assert usd["median_hold_days_winners"] == 9          # median of 15 and 3
    assert usd["median_hold_days_losers"] == 30
    assert usd["disposition_ratio"] == 3.33              # 30 / 9
    assert usd["trades_per_month"] == {"2026-01": 3, "2026-02": 1, "2026-03": 3}
    assert tl["n_losers"] == 1 and tl["median_hold_days_winners"] is None
    assert tl["disposition_ratio"] is None               # no winners -> no ratio


def test_empty_trades():
    assert behavior_metrics(pd.DataFrame()) == {"by_currency": {}, "unmatched_sells": []}
