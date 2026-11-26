import sqlite3

import pytest

from src.journal import db

RESULT = {"result": {"rationale": "r", "label": "fomo", "evidence": "now", "missing_checks": ["valuation"],
                     "questions": [{"text": "How did you value it?", "check": "valuation"}]}, "model": "m"}
TRADE = {"date": "2026-11-20", "ticker": "NVDA", "market": "US", "side": "buy", "quantity": 2,
         "price": 180.5, "currency": "USD", "fee": 1.0, "note_id": None}


@pytest.fixture
def conn():
    return db.connect(":memory:")


def test_note_with_latest_analysis(conn):
    note_id = db.add_note(conn, "2026-11-20", " nvda ", "US", "buy", "Buying now before earnings.")
    db.add_analysis(conn, note_id, {"error": "503", "model": "m"}, "h1")
    db.add_analysis(conn, note_id, RESULT, "h2")
    [note] = db.list_notes(conn)
    assert note["ticker"] == "NVDA"                                    # cleaned on save
    assert note["analysis"]["label"] == "fomo" and note["analysis"]["prompt_hash"] == "h2"
    assert note["analysis"]["questions"][0]["check"] == "valuation"    # JSON comes back as a list


def test_failed_analysis_is_stored_with_its_error(conn):
    note_id = db.add_note(conn, "2026-11-20", "THYAO", "BIST", "hold", "Waiting.")
    db.add_analysis(conn, note_id, {"error": "API call failed", "model": "m"}, "h")
    analysis = db.latest_analysis(conn, note_id)
    assert analysis["label"] is None and analysis["error"] == "API call failed"


def test_invalid_values_are_rejected_by_the_schema(conn):
    with pytest.raises(sqlite3.IntegrityError):
        db.add_note(conn, "2026-11-20", "NVDA", "NASDAQ", "buy", "text")      # unknown market
    with pytest.raises(sqlite3.IntegrityError):
        db.add_note(conn, "2026-11-20", "NVDA", "US", "buy", "   ")           # empty note
    with pytest.raises(sqlite3.IntegrityError):
        db.add_analysis(conn, 999, RESULT, "h")                               # note does not exist


def test_same_trade_is_imported_once(conn):
    assert db.add_trade(conn, TRADE) is True
    assert db.add_trade(conn, TRADE) is False
    assert db.add_trade(conn, {**TRADE, "quantity": 3}) is True
    assert len(db.list_trades(conn)) == 2


def test_deleting_a_note_keeps_its_trades(conn):
    note_id = db.add_note(conn, "2026-11-20", "NVDA", "US", "buy", "text")
    db.add_trade(conn, {**TRADE, "note_id": note_id})
    with conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    assert db.list_trades(conn)[0]["note_id"] is None
