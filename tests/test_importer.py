from pathlib import Path

import pytest

from src.journal import db
from src.journal.importer import import_trades

SAMPLE = Path(__file__).parent / "fixtures" / "trades_sample.csv"


@pytest.fixture
def conn():
    return db.connect(":memory:")


def test_valid_rows_are_imported_and_invalid_rows_reported(conn):
    report = import_trades(conn, SAMPLE)
    assert report["imported"] == 3
    assert [line for line, _ in report["rejected"]] == [4, 5, 6]
    assert "quantity" in report["rejected"][0][1]
    assert "market" in report["rejected"][1][1]
    assert "date" in report["rejected"][2][1]


def test_values_are_normalized(conn):
    import_trades(conn, SAMPLE)
    trades = db.list_trades(conn)
    assert trades[0]["ticker"] == "AVGO"           # lowercase input
    assert trades[1]["fee"] == 0                   # empty cell -> default


def test_reimporting_the_same_file_adds_nothing(conn):
    import_trades(conn, SAMPLE)
    report = import_trades(conn, SAMPLE)
    assert report["imported"] == 0
    assert report["duplicates"] == 3
    assert len(db.list_trades(conn)) == 3


def test_missing_column_rejects_the_whole_file(conn, tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("date,ticker,side\n2026-09-03,AVGO,buy\n")
    report = import_trades(conn, bad)
    assert report["imported"] == 0
    assert report["rejected"][0][0] == 1
    assert "market" in report["rejected"][0][1]


def test_unknown_note_id_is_rejected(conn, tmp_path):
    csv_file = tmp_path / "t.csv"
    csv_file.write_text("date,ticker,market,side,quantity,price,currency,note_id\n"
                        "2026-09-03,AVGO,US,buy,2,310.5,USD,999\n")
    report = import_trades(conn, csv_file)
    assert report["imported"] == 0
    assert report["rejected"] == [(2, "note_id: no note with id 999")]
