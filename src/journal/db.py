"""SQLite storage for the journal (REQ-020, REQ-022). Python standard library only.

Three tables, each answering one question:
- notes:    what did I decide, and why?            (written by me)
- analyses: what did the model say about a note?    (one row per analysis run, never overwritten)
- trades:   what did I actually do?                 (imported from CSV, REQUIREMENTS §7.1)

Metrics are never stored: they are computed from `trades` when needed, so they can't go stale.
The real database lives in the git-ignored data/private/. The demo uses ":memory:" instead.
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.data.load import ROOT

DB_PATH = ROOT / "data" / "private" / "journal.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id            INTEGER PRIMARY KEY,
    decision_date TEXT NOT NULL,                                   -- ISO date of the decision
    created_at    TEXT NOT NULL,                                   -- when the note was written
    ticker        TEXT NOT NULL,
    market        TEXT NOT NULL CHECK (market IN ('US', 'BIST')),
    side          TEXT NOT NULL CHECK (side IN ('buy', 'sell', 'hold')),
    text          TEXT NOT NULL CHECK (length(trim(text)) > 0)
);

CREATE TABLE IF NOT EXISTS analyses (
    id             INTEGER PRIMARY KEY,
    note_id        INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    created_at     TEXT NOT NULL,
    model          TEXT NOT NULL,
    prompt_hash    TEXT NOT NULL,
    label          TEXT,                                           -- NULL when the analysis failed
    evidence       TEXT,
    rationale      TEXT,
    missing_checks TEXT NOT NULL DEFAULT '[]',                     -- JSON list
    questions      TEXT NOT NULL DEFAULT '[]',                     -- JSON list of {text, check}
    error          TEXT
);

CREATE TABLE IF NOT EXISTS trades (
    id        INTEGER PRIMARY KEY,
    date      TEXT NOT NULL,
    ticker    TEXT NOT NULL,
    market    TEXT NOT NULL CHECK (market IN ('US', 'BIST')),
    side      TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity  REAL NOT NULL CHECK (quantity > 0),
    price     REAL NOT NULL CHECK (price > 0),
    currency  TEXT NOT NULL CHECK (currency IN ('USD', 'TRY')),
    fee       REAL NOT NULL DEFAULT 0 CHECK (fee >= 0),
    note_id   INTEGER REFERENCES notes(id) ON DELETE SET NULL,
    row_hash  TEXT NOT NULL UNIQUE                                 -- same CSV row twice -> imported once
);
"""


def connect(path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Open (and create if needed) the database. Pass ":memory:" for tests and the demo."""
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row            # rows behave like dicts: row["ticker"]
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite ignores REFERENCES unless this is on
    conn.executescript(SCHEMA)
    return conn


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")

# ---------------------------------------------------------------------------
# Notes and analyses
# ---------------------------------------------------------------------------


def add_note(conn, decision_date: str, ticker: str, market: str, side: str, text: str) -> int:
    """Save a note and return its id."""
    with conn:                                # commits on success, rolls back on error
        cur = conn.execute(
            "INSERT INTO notes (decision_date, created_at, ticker, market, side, text) VALUES (?, ?, ?, ?, ?, ?)",
            (decision_date, now(), ticker.strip().upper(), market, side, text.strip()),
        )
    return cur.lastrowid


def add_analysis(conn, note_id: int, out: dict, prompt_hash: str) -> int:
    """Store the output of src.llm.gemini.analyze() for a note: either a result or an error."""
    result = out.get("result") or {}
    with conn:
        cur = conn.execute(
            """INSERT INTO analyses (note_id, created_at, model, prompt_hash, label, evidence, rationale,
                                     missing_checks, questions, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (note_id, now(), out.get("model", ""), prompt_hash, result.get("label"), result.get("evidence"),
             result.get("rationale"), json.dumps(result.get("missing_checks", [])),
             json.dumps(result.get("questions", [])), out.get("error")),
        )
    return cur.lastrowid


def _analysis_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["missing_checks"], d["questions"] = json.loads(d["missing_checks"]), json.loads(d["questions"])
    return d


def latest_analysis(conn, note_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM analyses WHERE note_id = ? ORDER BY id DESC LIMIT 1", (note_id,)).fetchone()
    return _analysis_dict(row) if row else None


def list_notes(conn) -> list[dict]:
    """All notes, newest decision first, each with its latest analysis (or None)."""
    rows = conn.execute("SELECT * FROM notes ORDER BY decision_date DESC, id DESC").fetchall()
    return [{**dict(r), "analysis": latest_analysis(conn, r["id"])} for r in rows]

# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------

TRADE_FIELDS = ["date", "ticker", "market", "side", "quantity", "price", "currency", "fee", "note_id"]


def row_hash(trade: dict) -> str:
    """Fingerprint of the fields that identify a trade (note_id excluded: linking a note is not a new trade)."""
    key = "|".join(str(trade[f]) for f in TRADE_FIELDS if f != "note_id")
    return hashlib.sha256(key.encode()).hexdigest()


def add_trade(conn, trade: dict) -> bool:
    """Insert one already-validated trade. Returns False if the same trade was imported before."""
    values = [trade.get(f) for f in TRADE_FIELDS]
    with conn:
        cur = conn.execute(
            f"INSERT OR IGNORE INTO trades ({', '.join(TRADE_FIELDS)}, row_hash) VALUES ({', '.join('?' * 10)})",
            (*values, row_hash(trade)),
        )
    return cur.rowcount == 1


def list_trades(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM trades ORDER BY date, id").fetchall()]
