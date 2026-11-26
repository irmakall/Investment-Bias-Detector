"""CSV trade import (REQ-022). Schema: REQUIREMENTS §7.1.

Policy: valid rows are imported, invalid rows are reported with their line number and skipped.
A single typo should not block a whole file; the report says exactly which rows to fix.
Exception: if a required column is missing, nothing can be read correctly, so the whole file is rejected.

A future Midas importer is a separate adapter that produces rows in this schema.
"""

import csv
import sqlite3
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from src.journal import db

REQUIRED_COLUMNS = {"date", "ticker", "market", "side", "quantity", "price", "currency"}


class TradeRow(BaseModel):
    """One CSV row. Pydantic converts the text values to real types and rejects invalid ones."""

    date: date
    ticker: str = Field(min_length=1)
    market: Literal["US", "BIST"]
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    currency: Literal["USD", "TRY"]
    fee: float = Field(default=0, ge=0)
    note_id: int | None = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


def _clean(row: dict) -> dict:
    """Strip whitespace and drop empty cells, so optional fields fall back to their defaults."""
    return {k.strip(): v.strip() for k, v in row.items() if k and v is not None and v.strip() != ""}


def _first_error(e: ValidationError) -> str:
    err = e.errors()[0]
    field = ".".join(str(p) for p in err["loc"]) or "row"
    return f"{field}: {err['msg']}"


def import_trades(conn: sqlite3.Connection, csv_path: str | Path) -> dict:
    """Import trades from a CSV file. Returns {"imported", "duplicates", "rejected": [(line_no, reason)]}."""
    imported, duplicates, rejected = 0, 0, []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:   # utf-8-sig: ignores the BOM Excel adds
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - {c.strip() for c in (reader.fieldnames or [])}
        if missing:
            return {"imported": 0, "duplicates": 0, "rejected": [(1, f"missing columns: {', '.join(sorted(missing))}")]}

        for line_no, row in enumerate(reader, start=2):           # line 1 is the header
            try:
                trade = TradeRow(**_clean(row))
            except ValidationError as e:
                rejected.append((line_no, _first_error(e)))
                continue

            try:
                # mode="json" gives plain values ("2026-09-03", 2.0), so the same trade always hashes the same
                if db.add_trade(conn, trade.model_dump(mode="json")):
                    imported += 1
                else:
                    duplicates += 1
            except sqlite3.IntegrityError:                         # e.g. note_id points to a note that doesn't exist
                rejected.append((line_no, f"note_id: no note with id {trade.note_id}"))

    return {"imported": imported, "duplicates": duplicates, "rejected": rejected}
