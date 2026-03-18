#!/usr/bin/env python3
"""
seed_data.py
Populate the inventory database with demo items for the lab presentation.

Usage (from any directory):
    python3 seed_data.py [--clear]

The --clear flag wipes all existing data before seeding.
"""

import sys
import time
import argparse

# Make sure the package is importable when run directly
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dexter_inventory.inventory_db import init_db, add_item, clear_all, get_stock


def seed():
    parser = argparse.ArgumentParser(description="Seed the Dexter inventory database")
    parser.add_argument("--clear", action="store_true", help="Clear all data first")
    args = parser.parse_args()

    init_db()

    if args.clear:
        clear_all()
        print("✓ Database cleared")

    now = time.time()
    DAY = 86400.0   # seconds per day

    items = [
        # (name, slot, expiry_offset_days)   None = no expiry
        ("Box A – Resistors",    0,  5.0),   # expires in 5 days
        ("Box B – Capacitors",   1,  2.0),   # expires in 2 days (FEFO picks this first)
        ("Box C – LEDs",         2, None),   # no expiry
        ("Box D – Arduino Nano", 3, 10.0),   # expires in 10 days
    ]

    # Simulate different arrival times (Box A arrived first → FIFO picks it first)
    arrival_offsets = [-3 * DAY, -2 * DAY, -1 * DAY, 0]  # days ago

    print("\nSeeding inventory:")
    print("-" * 50)
    for (name, slot, expiry_days), arrival_offset in zip(items, arrival_offsets):
        try:
            expiry_ts = (now + expiry_days * DAY) if expiry_days is not None else None
            item_id   = add_item.__wrapped__(name, slot, expiry_ts) \
                        if hasattr(add_item, "__wrapped__") else _add_with_custom_arrival(
                            name, slot, now + arrival_offset, expiry_ts
                        )
            expiry_str = f"{expiry_days:.0f} days" if expiry_days else "no expiry"
            print(f"  Slot {slot}: {name:30s}  expiry={expiry_str}")
        except ValueError as e:
            print(f"  ⚠ Skipping slot {slot}: {e}")

    print("-" * 50)
    stock = get_stock()
    print(f"✓ {len(stock)} items now in stock\n")
    print("FIFO order (oldest first):")
    for i, row in enumerate(stock, 1):
        age_days = (now - row["arrival_ts"]) / DAY
        print(f"  {i}. Slot {row['slot']} – {row['name']}  (arrived {age_days:.1f} days ago)")

    print("\nFEFO order (soonest expiry first):  run dispatch_engine.get_fefo_item()")


def _add_with_custom_arrival(name, slot, arrival_ts, expiry_ts):
    """Direct DB insert to allow custom arrival timestamp for demo."""
    import sqlite3
    import uuid
    from dexter_inventory.inventory_db import DB_PATH
    item_id = uuid.uuid4().hex
    with sqlite3.connect(DB_PATH) as conn:
        # Check slot free
        row = conn.execute(
            "SELECT id FROM items WHERE slot=? AND dispatched=0", (slot,)
        ).fetchone()
        if row:
            raise ValueError(f"Slot {slot} already occupied")
        conn.execute(
            """INSERT INTO items (id, name, arrival_ts, expiry_ts, slot)
               VALUES (?, ?, ?, ?, ?)""",
            (item_id, name, arrival_ts, expiry_ts, slot),
        )
    return item_id


if __name__ == "__main__":
    seed()
