"""
dispatch_engine.py
Pure-Python dispatch decision layer.  No ROS dependency – fully testable standalone.

JOINT VALUE TABLE  (IK-verified, z = L0+L1*cos(j2)+L2*cos(j2+j3))
────────────────────────────────────────────────────────────────────
L0=0.657 m (base to joint_2)
L1=0.80  m (joint_2 to joint_3)
L2=0.82  m (joint_3 to claw_support)

All 4 slots have the same radial distance r = 1.229 m from the arm base,
so j2 and j3 are IDENTICAL for all slots.  Only j1 (base yaw) changes.

j2=-0.5502, j3=-1.1711 → z = 0.657+0.80*cos(-0.55)+0.82*cos(-1.72) = 1.216 m  ✓
j2=-0.5502, j3=-1.0000 → z = 0.657+0.80*cos(-0.55)+0.82*cos(-1.55) = 1.355 m  ✓ (hover)

         j1        j2       j3       world (x, y) m
Slot 0  -0.5496  -0.5502  -1.1711   (1.048, -0.642)
Slot 1  -0.1800  -0.5500  -1.1714   (1.209, -0.220)
Slot 2  +0.1800  -0.5500  -1.1714   (1.209, +0.220)
Slot 3  +0.5496  -0.5502  -1.1711   (1.048, +0.642)
Drop    +1.0122  -0.5502  -1.1711   (0.664,  1.034)
────────────────────────────────────────────────────────────────────
"""

import time
from typing import Optional, Tuple, Dict, Any

from dexter_inventory.inventory_db import (
    get_fifo_item,
    get_fefo_item,
    mark_dispatched,
    stock_count,
)


# ── Arm configuration ─────────────────────────────────────────────────────────

SLOT_POSES: Dict[int, Dict[str, list]] = {
    # j2 and j3 BOTH NEGATIVE: j2 tilts arm toward shelf, j3 folds elbow to correct height
    0: {
        "arm":            [-0.5496, -0.5502, -1.1711],  # z=1.216 m
        "gripper_open":   [0.0],
        "gripper_closed": [-0.7],
    },
    1: {
        "arm":            [-0.1800, -0.5500, -1.1714],
        "gripper_open":   [0.0],
        "gripper_closed": [-0.7],
    },
    2: {
        "arm":            [ 0.1800, -0.5500, -1.1714],
        "gripper_open":   [0.0],
        "gripper_closed": [-0.7],
    },
    3: {
        "arm":            [ 0.5496, -0.5502, -1.1711],
        "gripper_open":   [0.0],
        "gripper_closed": [-0.7],
    },
}

# Hover ≈ 14 cm above pick (same j1, j3 less negative → arm slightly higher)
SLOT_HOVER: Dict[int, list] = {
    0: [-0.5496, -0.5502, -1.0000],   # z≈1.355 m
    1: [-0.1800, -0.5500, -1.0000],
    2: [ 0.1800, -0.5500, -1.0000],
    3: [ 0.5496, -0.5502, -1.0000],
}

# Dispatch tray at world (0.664, 1.034): j1=atan2(1.034,0.664)≈1.01 rad
# r_drop = sqrt(0.664²+1.034²) = 1.229 m  (same as shelf slots)
# → identical j2/j3, just j1 points toward tray
DROP_ZONE_HOVER: list = [1.0122, -0.5502, -1.0000]   # z≈1.355 m above tray
DROP_ZONE_PLACE: list = [1.0122, -0.5502, -1.1711]   # z≈1.216 m at tray

HOME_POSE: list = [0.00, 0.00, 0.00]   # arm pointing straight up (safe park)

LOW_STOCK_THRESHOLD = 1


# ── Public API ────────────────────────────────────────────────────────────────

def select_item(mode: str) -> Optional[Any]:
    mode = mode.upper()
    if mode == "FIFO":
        return get_fifo_item()
    elif mode == "FEFO":
        return get_fefo_item()
    else:
        raise ValueError(f"Unknown mode: {mode!r}.  Use 'FIFO' or 'FEFO'.")


def build_motion_sequence(slot: int) -> list:
    """
    Return the ordered list of motion steps for picking from *slot*
    and delivering to the dispatch tray.
    """
    if slot not in SLOT_POSES:
        raise ValueError(f"Invalid slot {slot}. Valid: {list(SLOT_POSES)}")

    pose = SLOT_POSES[slot]

    return [
        # 1. Open gripper at home
        {
            "label":   "open gripper at home",
            "arm":     HOME_POSE,
            "gripper": pose["gripper_open"],
        },
        # 2. Hover above slot
        {
            "label":   f"hover above slot {slot}  (z≈1.36 m)",
            "arm":     SLOT_HOVER[slot],
            "gripper": pose["gripper_open"],
        },
        # 3. Descend to pick
        {
            "label":   f"descend to slot {slot}  (z≈1.22 m)",
            "arm":     pose["arm"],
            "gripper": pose["gripper_open"],
        },
        # 4. Close gripper
        {
            "label":   f"grip item at slot {slot}",
            "arm":     pose["arm"],
            "gripper": pose["gripper_closed"],
        },
        # 5. Lift to hover
        {
            "label":   f"lift from slot {slot}",
            "arm":     SLOT_HOVER[slot],
            "gripper": pose["gripper_closed"],
        },
        # 6. Hover above drop zone
        {
            "label":   "approach drop zone  (z≈1.36 m)",
            "arm":     DROP_ZONE_HOVER,
            "gripper": pose["gripper_closed"],
        },
        # 7. Descend to tray
        {
            "label":   "place at drop zone  (z≈1.22 m)",
            "arm":     DROP_ZONE_PLACE,
            "gripper": pose["gripper_closed"],
        },
        # 8. Release
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
    item = select_item(mode)
    if item is None:
        return False, "No items in stock to dispatch.", None

    slot  = item["slot"]
    steps = build_motion_sequence(slot)
    info  = {
        "item_id":   item["id"],
        "item_name": item["name"],
        "slot":      slot,
        "mode":      mode.upper(),
        "expiry_ts": item["expiry_ts"],
        "steps":     steps,
    }
    return True, f"Dispatching '{item['name']}' from slot {slot} ({mode.upper()})", info


def check_low_stock() -> Tuple[bool, int]:
    count = stock_count()
    return count <= LOW_STOCK_THRESHOLD, count


def format_expiry(ts: Optional[float]) -> str:
    if ts is None:
        return "no expiry"
    delta = ts - time.time()
    if delta < 0:
        return "EXPIRED"
    days  = int(delta // 86400)
    hours = int((delta % 86400) // 3600)
    return f"{days}d {hours}h remaining"
