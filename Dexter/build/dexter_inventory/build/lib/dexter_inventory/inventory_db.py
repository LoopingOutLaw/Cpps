"""
inventory_db.py
SQLite database layer for the Dexter FIFO/FEFO inventory system.

Table schema
------------
items
  id            TEXT PRIMARY KEY   (uuid4 hex)
  name          TEXT
  arrival_ts    REAL               (Unix timestamp – used for FIFO)
  expiry_ts     REAL               (Unix timestamp – used for FEFO; NULL = no expiry)
  slot          INTEGER            (0-3, shelf slot where the item sits)
  dispatched    INTEGER            (0 = in stock, 1 = dispatched)
  dispatched_ts REAL               (Unix timestamp of dispatch; NULL if in stock)

dispatch_log
  id            INTEGER PRIMARY KEY AUTOINCREMENT
  item_id       TEXT
  item_name     TEXT
  mode          TEXT               ("FIFO" or "FEFO")
  slot          INTEGER
  ts            REAL               (Unix timestamp)
"""

import sqlite3
import uuid
import time
import os
from typing import Optional


DB_PATH = os.path.join(os.path.expanduser("~"), "dexter_inventory.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id            TEXT    PRIMARY KEY,
                name          TEXT    NOT NULL,
                arrival_ts    REAL    NOT NULL,
                expiry_ts     REAL,
                slot          INTEGER NOT NULL,
                dispatched    INTEGER NOT NULL DEFAULT 0,
                dispatched_ts REAL
            );

            CREATE TABLE IF NOT EXISTS dispatch_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id   TEXT    NOT NULL,
                item_name TEXT    NOT NULL,
                mode      TEXT    NOT NULL,
                slot      INTEGER NOT NULL,
                ts        REAL    NOT NULL
            );
        """)


def add_item(name: str, slot: int, expiry_ts: Optional[float] = None) -> str:
    """
    Insert a new item into the given slot.
    Returns the generated item id.
    Raises ValueError if the slot is already occupied.
    """
    init_db()
    if slot < 0 or slot > 3:
        raise ValueError(f"Slot must be 0-3, got {slot}")

    with _connect() as conn:
        # Check slot is free
        row = conn.execute(
            "SELECT id FROM items WHERE slot=? AND dispatched=0", (slot,)
        ).fetchone()
        if row:
            raise ValueError(f"Slot {slot} is already occupied by item {row['id']}")

        item_id = uuid.uuid4().hex
        conn.execute(
            """INSERT INTO items (id, name, arrival_ts, expiry_ts, slot)
               VALUES (?, ?, ?, ?, ?)""",
            (item_id, name, time.time(), expiry_ts, slot),
        )
    return item_id


def get_fifo_item() -> Optional[sqlite3.Row]:
    """Return the in-stock item with the earliest arrival timestamp."""
    init_db()
    with _connect() as conn:
        return conn.execute(
            """SELECT * FROM items
               WHERE dispatched=0
               ORDER BY arrival_ts ASC
               LIMIT 1"""
        ).fetchone()


def get_fefo_item() -> Optional[sqlite3.Row]:
    """
    Return the in-stock item with the earliest expiry date.
    Items with no expiry are returned last (treated as never-expiring).
    """
    init_db()
    with _connect() as conn:
        return conn.execute(
            """SELECT * FROM items
               WHERE dispatched=0
               ORDER BY
                   CASE WHEN expiry_ts IS NULL THEN 1 ELSE 0 END ASC,
                   expiry_ts ASC
               LIMIT 1"""
        ).fetchone()


def mark_dispatched(item_id: str, mode: str) -> None:
    """Mark an item as dispatched and write a dispatch log entry."""
    init_db()
    now = time.time()
    with _connect() as conn:
        row = conn.execute(
            "SELECT name, slot FROM items WHERE id=?", (item_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Item {item_id} not found")

        conn.execute(
            "UPDATE items SET dispatched=1, dispatched_ts=? WHERE id=?",
            (now, item_id),
        )
        conn.execute(
            """INSERT INTO dispatch_log (item_id, item_name, mode, slot, ts)
               VALUES (?, ?, ?, ?, ?)""",
            (item_id, row["name"], mode, row["slot"], now),
        )


def get_stock() -> list:
    """Return all in-stock items ordered by arrival time."""
    init_db()
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM items WHERE dispatched=0 ORDER BY arrival_ts ASC"
        ).fetchall()


def get_dispatch_log(limit: int = 20) -> list:
    """Return the most recent dispatch log entries."""
    init_db()
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM dispatch_log ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()


def stock_count() -> int:
    """Return number of items currently in stock."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM items WHERE dispatched=0"
        ).fetchone()
        return row["cnt"] if row else 0


def clear_all() -> None:
    """Wipe all data – useful for demo resets."""
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM dispatch_log")
