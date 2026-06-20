# tests/test_db.py
from unittest.mock import MagicMock
from db import MySQL


def test_execute_returns_lastrowid():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    cursor.lastrowid = 42
    db = MySQL(conn)
    rowid = db.execute("INSERT INTO t (a) VALUES (%s)", (1,))
    cursor.execute.assert_called_once_with("INSERT INTO t (a) VALUES (%s)", (1,))
    assert rowid == 42


def test_query_returns_rows():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchall.return_value = [{"village_id": 1}]
    db = MySQL(conn)
    rows = db.query("SELECT village_id FROM task_status WHERE status='done'")
    assert rows == [{"village_id": 1}]


def test_query_one_returns_single():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = {"id": 7}
    db = MySQL(conn)
    row = db.query_one("SELECT * FROM vill_village WHERE id=%s", (7,))
    assert row == {"id": 7}
