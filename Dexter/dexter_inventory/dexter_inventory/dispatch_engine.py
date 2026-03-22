"""
dispatch_engine.py
Pure-Python dispatch decision layer.  No ROS dependency – fully testable standalone.

SLOT → ARM JOINT MAPPING (IK-calculated for box positions)
----------------------------------------------------------
Robot link lengths: L0=0.657m (base), L1=0.80m (link1), L2=0.82m (link2)
Gripper pick height: z=1.216m (boxes at z=1.156m, 6cm clearance)

         joint_1  joint_2  joint_3   world position (x, y)
Slot 0   -0.55    +0.55    +1.17     (1.048, -0.642)
Slot 1   -0.18    +0.55    +1.17     (1.209, -0.220)
Slot 2   +0.18    +0.55    +1.17     (1.209, +0.220)
Slot 3   +0.55    +0.55    +1.17     (1.048, +0.642)

Drop zone (to the side at y>0):
         +1.01    +0.20    +1.65     (0.5, 0.8)
"""

import time
from typing import Optional, Tuple, Dict, Any

from dexter_inventory.inventory_db import (
    get_fifo_item,
    get_fefo_item,
    mark_dispatched,
    stock_count,
)


# ── Arm configuration ────────────────────────────────────────────────────────
# IK-calculated joint positions for each slot (gripper at z=1.216m)

SLOT_POSES: Dict[int, Dict[str, list]] = {
    0: {"arm": [-0.5496,  0.5502,  1.1711], "gripper_open": [0.0, 0.0], "gripper_closed": [-0.7, 0.7]},
    1: {"arm": [-0.1800,  0.5500,  1.1714], "gripper_open": [0.0, 0.0], "gripper_closed": [-0.7, 0.7]},
    2: {"arm": [ 0.1800,  0.5500,  1.1714], "gripper_open": [0.0, 0.0], "gripper_closed": [-0.7, 0.7]},
    3: {"arm": [ 0.5496,  0.5502,  1.1711], "gripper_open": [0.0, 0.0], "gripper_closed": [-0.7, 0.7]},
}

# Hover height – arm position 15cm above each slot (for safe transit)
SLOT_HOVER: Dict[int, list] = {
    0: [-0.5496,  0.5371,  1.0073],
    1: [-0.1800,  0.5368,  1.0077],
    2: [ 0.1800,  0.5368,  1.0077],
    3: [ 0.5496,  0.5371,  1.0073],
}

DROP_ZONE_HOVER:  list = [1.0122, 0.1599, 1.5096]  # hover above drop zone
DROP_ZONE_PLACE:  list = [1.0122, 0.1951, 1.6547]  # drop position (x=0.5, y=0.8)
HOME_POSE:        list = [0.00,  0.00,  0.00]

LOW_STOCK_THRESHOLD = 1     # alert when at or below this many items


# ── Public API ────────────────────────────────────────────────────────────────

def select_item(mode: str) -> Optional[Any]:
    """
    Select the next item to dispatch according to *mode*.

    Parameters
    ----------
    mode : "FIFO" | "FEFO"

    Returns
    -------
    sqlite3.Row or None
    """
    mode = mode.upper()
    if mode == "FIFO":
        return get_fifo_item()
    elif mode == "FEFO":
        return get_fefo_item()
    else:
        raise ValueError(f"Unknown dispatch mode: {mode!r}. Use 'FIFO' or 'FEFO'.")


def build_motion_sequence(slot: int) -> list:
    """
    Return the ordered list of motion steps the arm must execute to pick
    from *slot* and deliver to the drop zone.

    Each step is a dict:
        {
            "label":   str,          # human-readable description
            "arm":     [j1, j2, j3], # target joint positions (radians)
            "gripper": [j4, j5],     # target gripper position
        }
    """
    if slot not in SLOT_POSES:
        raise ValueError(f"Invalid slot {slot}. Valid slots: {list(SLOT_POSES)}")

    pose = SLOT_POSES[slot]

    return [
        # 1. Open gripper at home
        {
            "label":   "open gripper at home",
            "arm":     HOME_POSE,
            "gripper": pose["gripper_open"],
        },
        # 2. Hover above target slot
        {
            "label":   f"hover above slot {slot}",
            "arm":     SLOT_HOVER[slot],
            "gripper": pose["gripper_open"],
        },
        # 3. Descend to pick position
        {
            "label":   f"descend to slot {slot}",
            "arm":     pose["arm"],
            "gripper": pose["gripper_open"],
        },
        # 4. Close gripper – grab item
        {
            "label":   f"grip item at slot {slot}",
            "arm":     pose["arm"],
            "gripper": pose["gripper_closed"],
        },
        # 5. Lift back to hover height (with item)
        {
            "label":   f"lift from slot {slot}",
            "arm":     SLOT_HOVER[slot],
            "gripper": pose["gripper_closed"],
        },
        # 6. Hover above drop zone
        {
            "label":   "approach drop zone",
            "arm":     DROP_ZONE_HOVER,
            "gripper": pose["gripper_closed"],
        },
        # 7. Descend to drop position
        {
            "label":   "place at drop zone",
            "arm":     DROP_ZONE_PLACE,
            "gripper": pose["gripper_closed"],
        },
        # 8. Open gripper – release
        {
            "label":   "release item",
            "arm":     DROP_ZONE_PLACE,
            "gripper": pose["gripper_open"],
        },
        # 9. Return home
        {
            "label":   "return to home",
            "arm":     HOME_POSE,
            "gripper": pose["gripper_open"],
        },
    ]


def dispatch(mode: str) -> Tuple[bool, str, Optional[dict]]:
    """
    High-level dispatch call:  select item → build motion sequence → mark dispatched.

    Returns
    -------
    (success, message, info_dict)
        info_dict keys: item_id, item_name, slot, mode, steps
    """
    item = select_item(mode)
    if item is None:
        return False, "No items in stock to dispatch.", None

    slot = item["slot"]
    steps = build_motion_sequence(slot)

    info = {
        "item_id":   item["id"],
        "item_name": item["name"],
        "slot":      slot,
        "mode":      mode.upper(),
        "expiry_ts": item["expiry_ts"],
        "steps":     steps,
    }

    # DB update happens *after* arm completes – caller is responsible for
    # calling mark_dispatched() once execution succeeds.
    return True, f"Dispatching '{item['name']}' from slot {slot} ({mode.upper()})", info


def check_low_stock() -> Tuple[bool, int]:
    """Return (is_low, current_count)."""
    count = stock_count()
    return count <= LOW_STOCK_THRESHOLD, count


def format_expiry(ts: Optional[float]) -> str:
    """Human-readable expiry string."""
    if ts is None:
        return "no expiry"
    delta = ts - time.time()
    if delta < 0:
        return "EXPIRED"
    days = int(delta // 86400)
    hours = int((delta % 86400) // 3600)
    return f"{days}d {hours}h remaining"
