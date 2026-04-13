#!/usr/bin/env python3
"""
web_interface.py - Dexter FEFO/FIFO Inventory Control Dashboard

Dispatch flow (FIXED):
    Browser → POST /inventory/dispatch → dispatch_via_visual_servo()
           → publishes Int32 to /visual_servo/pick_request
           → visual_servo_node.py does the actual pick-and-place
           → DB marked dispatched immediately (optimistic)

Shelf-life additions:
    - Every item now shows arrival date, total shelf life (days), remaining
    - Add-item form accepts shelf_life_days (auto-computes expiry from arrival)

Routes
------
GET  /                         → Dashboard
POST /task                     { task_number: 0|1|2 }
POST /inventory/dispatch       { mode: "FIFO"|"FEFO"|"RL" }
POST /inventory/add_item       { item_name, slot, shelf_life_days?, expiry_ts? }
POST /inventory/clear
GET  /inventory/state
GET  /inventory/rl_recommendation
GET  /health
"""

from __future__ import annotations

import datetime
import os
import random
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, render_template, jsonify, request as flask_request

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String, Int32

try:
    from dexter_msgs.action import DexterTask
    _ACTION_AVAILABLE = True
except ImportError:
    _ACTION_AVAILABLE = False
    DexterTask = None

try:
    from dexter_msgs.srv import DispatchItem, AddItem as AddItemSrv
    _SRV_AVAILABLE = True
except ImportError:
    _SRV_AVAILABLE = False

try:
    from dexter_inventory.inventory_db import (
        init_db, get_stock, get_dispatch_log,
        stock_count, clear_all, add_item as db_add_item,
        reset_with_defaults, get_fifo_item, get_fefo_item, mark_dispatched,
    )
    from dexter_inventory.dispatch_engine import format_expiry
    from dexter_inventory.ml_forecast import DemandForecaster
    _INV_AVAILABLE = True
except ImportError:
    _INV_AVAILABLE = False

    def init_db() -> None: pass
    def get_stock() -> list: return []
    def get_dispatch_log(limit: int = 10) -> list: return []
    def stock_count() -> int: return 0
    def clear_all() -> None: pass
    def reset_with_defaults() -> None: pass
    def db_add_item(name: str, slot: int, expiry: Any = None) -> str: return ""
    def get_fifo_item(): return None
    def get_fefo_item(): return None
    def mark_dispatched(item_id: str, mode: str) -> None: pass
    def format_expiry(ts: Any) -> str: return "N/A"

    class DemandForecaster:
        def train(self) -> bool: return False
        def reorder_recommendation(self) -> dict:
            return {"reorder": False, "predicted_demand": 0,
                    "current_stock": 0, "order_quantity": 0, "reason": "N/A"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_date(ts: Optional[float]) -> str:
    """Return human-readable local date from Unix timestamp."""
    if ts is None:
        return "—"
    return datetime.datetime.fromtimestamp(ts).strftime("%b %d, %Y")


def _shelf_life_days(arrival_ts: Optional[float], expiry_ts: Optional[float]) -> Optional[float]:
    """Total shelf life in days (expiry − arrival). None if either is missing."""
    if arrival_ts and expiry_ts:
        return round((expiry_ts - arrival_ts) / 86400, 1)
    return None


def _item_row(row) -> dict:
    """Convert a DB row into a JSON-safe dict enriched with shelf-life fields."""
    arrival = row["arrival_ts"]
    expiry  = row["expiry_ts"]
    return {
        "id":               row["id"],
        "name":             row["name"],
        "slot":             row["slot"],
        "arrival_ts":       arrival,
        "expiry_ts":        expiry,
        "expiry":           format_expiry(expiry),
        "arrival_date":     _fmt_date(arrival),
        "shelf_life_days":  _shelf_life_days(arrival, expiry),
    }


# ── RL Optimizer ──────────────────────────────────────────────────────────────

class RLDispatchOptimizer:
    ACTIONS = ["FIFO", "FEFO", "HOLD"]
    ALPHA = 0.1
    GAMMA = 0.95
    EPSILON = 0.1

    def __init__(self):
        self.q_table: Dict[Tuple, Dict[str, float]] = {}
        self._lock = threading.Lock()

    def _get_state(self, items: List[dict]) -> Tuple:
        if not items:
            return (0, 0, 0)
        now = time.time()
        min_d = min(
            ((i["expiry_ts"] - now) / 86400 for i in items if i.get("expiry_ts")),
            default=float("inf"),
        )
        eb = 0 if min_d <= 0 else (1 if min_d <= 2 else (2 if min_d <= 7 else 3))
        cnt = len(items)
        sb = 0 if cnt == 0 else (1 if cnt <= 1 else (2 if cnt <= 3 else 3))
        return (eb, sb, 1)

    def _q(self, state: Tuple) -> Dict[str, float]:
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.ACTIONS}
        return self.q_table[state]

    def choose_action(self, items: List[dict], explore: bool = True) -> str:
        if not items:
            return "HOLD"
        state = self._get_state(items)
        if explore and random.random() < self.EPSILON:
            return random.choice(self.ACTIONS[:2])
        return max(self.ACTIONS[:2], key=lambda a: self._q(state)[a])

    def get_recommendation(self, items: List[dict]) -> dict:
        if not items:
            return {"action": "HOLD", "confidence": 1.0,
                    "reason": "No items in stock", "urgency": "none"}
        state = self._get_state(items)
        qv = self._q(state)
        action = self.choose_action(items, explore=False)
        confidence = min(1.0, 0.5 + abs(qv["FIFO"] - qv["FEFO"]) / 2)
        eb = state[0]
        if eb <= 1:
            urgency, reason = "critical", "Items expiring soon — FEFO recommended"
        elif eb == 2:
            urgency, reason = "warning", "Some items approaching expiry"
        else:
            urgency, reason = "normal", "No urgent expiries — FIFO maintains fairness"
        return {"action": action, "confidence": round(confidence, 2),
                "reason": reason, "urgency": urgency,
                "q_values": {k: round(v, 3) for k, v in qv.items()}}

    def calculate_reward(self, item: dict, mode: str) -> float:
        now = time.time()
        reward = 1.0
        if item.get("expiry_ts"):
            d = (item["expiry_ts"] - now) / 86400
            if d <= 0:
                reward -= 5.0
            elif d <= 2:
                reward += 2.0 if mode == "FEFO" else 1.0
            elif d <= 7:
                reward += 0.5 if mode == "FEFO" else 0.0
        age = (now - item.get("arrival_ts", now)) / 86400
        if age > 3 and mode == "FIFO":
            reward += 0.5
        return reward

    def update(self, state: Tuple, action: str, reward: float, next_state: Tuple):
        with self._lock:
            q = self._q(state)
            nq = self._q(next_state)
            q[action] += self.ALPHA * (reward + self.GAMMA * max(nq.values()) - q[action])


# ── Urgency Classifier ────────────────────────────────────────────────────────

class UrgencyClassifier:
    @staticmethod
    def classify(item: dict) -> dict:
        now = time.time()
        out = {"level": "LOW", "color": "#3fb950", "priority": 4,
               "reason": "No expiry set", "days_remaining": None}
        if not item.get("expiry_ts"):
            return out
        d = (item["expiry_ts"] - now) / 86400
        out["days_remaining"] = round(d, 1)
        if d <= 0:
            out.update({"level": "CRITICAL", "color": "#f85149",
                        "priority": 1, "reason": "EXPIRED"})
        elif d <= 2:
            out.update({"level": "HIGH", "color": "#d29922",
                        "priority": 2, "reason": f"Expiring in {d:.1f} days"})
        elif d <= 7:
            out.update({"level": "MEDIUM", "color": "#58a6ff",
                        "priority": 3, "reason": f"Expiring in {d:.1f} days"})
        else:
            out["reason"] = f"{d:.0f} days until expiry"
        return out

    @staticmethod
    def classify_all(items: List[dict]) -> dict:
        classified, summary = [], {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for item in items:
            c = UrgencyClassifier.classify(item)
            c["item_id"] = item.get("id")
            c["item_name"] = item.get("name")
            classified.append(c)
            summary[c["level"]] += 1
        classified.sort(key=lambda x: x["priority"])
        if summary["CRITICAL"] > 0:
            overall = {"status": "CRITICAL",
                       "message": f"{summary['CRITICAL']} item(s) expired!"}
        elif summary["HIGH"] > 0:
            overall = {"status": "WARNING",
                       "message": f"{summary['HIGH']} item(s) expiring soon"}
        else:
            overall = {"status": "OK",
                       "message": "All items within safe expiry range"}
        return {"items": classified, "summary": summary, "overall": overall}


# ── ROS Node ──────────────────────────────────────────────────────────────────

class WebInterface(Node):
    TASK_NAMES = {0: "Home/Wake", 1: "Pick", 2: "Sleep"}

    def __init__(self):
        super().__init__("web_interface")
        self._lock = threading.Lock()

        # Arm action client (for /task route)
        if _ACTION_AVAILABLE:
            self.arm_client = ActionClient(self, DexterTask, "task_server")
        else:
            self.arm_client = None

        # ── Visual servo publisher (THE fix) ──────────────────────────────────
        # This is what actually moves the arm to the right box position.
        # Publishing an Int32 slot number to this topic triggers the full
        # 8-phase visual-servo pick-and-place sequence in visual_servo_node.py
        self.pick_pub = self.create_publisher(Int32, "/visual_servo/pick_request", 10)

        # Inventory
        if _INV_AVAILABLE:
            reset_with_defaults()
            self.get_logger().info("DB reset with default inventory")
            self.forecaster = DemandForecaster()
        else:
            self.forecaster = None

        self.rl_optimizer       = RLDispatchOptimizer()
        self.urgency_classifier = UrgencyClassifier()

        self.get_logger().info("WebInterface ready  →  http://localhost:5000")

    # ── Arm task (Home / Pick / Sleep) ────────────────────────────────────────

    def send_task(self, task_number: int) -> Tuple[bool, str]:
        if not _ACTION_AVAILABLE or self.arm_client is None:
            return False, "DexterTask action not available"
        if not self._lock.acquire(blocking=False):
            return False, "Another task is running"
        try:
            if not self.arm_client.wait_for_server(timeout_sec=5.0):
                return False, "Task server not available"
            goal = DexterTask.Goal()
            goal.task_number = task_number
            name = self.TASK_NAMES.get(task_number, str(task_number))
            result_holder: dict = {}
            done = threading.Event()

            def _goal_cb(fut):
                gh = fut.result()
                if not gh or not gh.accepted:
                    result_holder.update({"ok": False, "msg": f"{name} rejected"})
                    done.set(); return
                gh.get_result_async().add_done_callback(_result_cb)

            def _result_cb(fut):
                try:
                    r = fut.result()
                    result_holder.update({"ok": r.result.success,
                                          "msg": f"{name} complete"})
                except Exception as e:
                    result_holder.update({"ok": False, "msg": str(e)})
                finally:
                    done.set()

            self.arm_client.send_goal_async(goal).add_done_callback(_goal_cb)
            done.wait(timeout=30.0)
            return result_holder.get("ok", False), result_holder.get("msg", "Timeout")
        finally:
            self._lock.release()

    # ── Dispatch via visual servo (THE FIX) ───────────────────────────────────

    def dispatch_via_visual_servo(self, mode: str) -> Tuple[bool, dict]:
        """
        Select the next item using FIFO/FEFO logic, publish its slot to
        /visual_servo/pick_request, and mark it dispatched in the DB.

        The visual_servo_node.py receives the Int32 slot number and
        executes the full 8-phase ArUco-guided pick-and-place sequence.
        """
        if not _INV_AVAILABLE:
            return False, {"msg": "Inventory module not available"}

        # Resolve RL → actual mode
        actual_mode = mode
        if mode == "RL":
            try:
                items = [dict(r) for r in get_stock()]
                rec = self.rl_optimizer.get_recommendation(items)
                actual_mode = rec["action"] if rec["action"] != "HOLD" else "FIFO"
            except Exception:
                actual_mode = "FIFO"

        # Select item
        try:
            item_row = get_fefo_item() if actual_mode == "FEFO" else get_fifo_item()
        except Exception as e:
            return False, {"msg": f"DB error: {e}"}

        if item_row is None:
            return False, {"msg": "No items in stock to dispatch"}

        item = dict(item_row)
        slot = item["slot"]

        # ── Publish pick request → visual_servo_node ──────────────────────────
        try:
            msg = Int32()
            msg.data = slot
            self.pick_pub.publish(msg)
            self.get_logger().info(
                f"[dispatch] Published /visual_servo/pick_request  slot={slot}  "
                f"item='{item['name']}'  mode={actual_mode}")
        except Exception as e:
            self.get_logger().error(f"Failed to publish pick request: {e}")
            return False, {"msg": f"Failed to trigger arm: {e}"}

        # ── Update DB & RL ─────────────────────────────────────────────────────
        reward = 0.0
        try:
            pre_items = [dict(r) for r in get_stock()]
            pre_state = self.rl_optimizer._get_state(pre_items)
            reward = self.rl_optimizer.calculate_reward(item, actual_mode)
            mark_dispatched(item["id"], actual_mode)
            post_items = [dict(r) for r in get_stock()]
            post_state = self.rl_optimizer._get_state(post_items)
            self.rl_optimizer.update(pre_state, actual_mode, reward, post_state)
        except Exception as e:
            self.get_logger().warning(f"DB/RL update warning: {e}")

        return True, {
            "msg":       f"Dispatching '{item['name']}' from slot {slot} ({actual_mode})",
            "item_name": item.get("name", ""),
            "item_id":   item.get("id", ""),
            "slot":      slot,
            "expiry":    format_expiry(item.get("expiry_ts")),
            "rl_reward": round(reward, 2),
        }


# ── Flask app ─────────────────────────────────────────────────────────────────

def _find_template_dir() -> str:
    try:
        from ament_index_python.packages import get_package_share_directory
        d = os.path.join(get_package_share_directory("dexter_remote"), "templates")
        if os.path.isdir(d):
            return d
    except Exception:
        pass
    this = Path(__file__).resolve()
    for parent in [this.parent.parent, this.parent]:
        d = parent / "templates"
        if d.is_dir():
            return str(d)
    return str(Path.cwd() / "templates")


app = Flask(__name__, template_folder=_find_template_dir())
ros_node: Optional[WebInterface] = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/task", methods=["POST"])
def handle_task():
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not ready"}), 503
    data = flask_request.get_json(silent=True) or {}
    task_num = data.get("task_number")
    if task_num is None:
        return jsonify({"success": False, "message": "Missing task_number"}), 400
    ok, msg = ros_node.send_task(int(task_num))
    return jsonify({"success": ok, "message": msg}), (200 if ok else 503)


@app.route("/inventory/dispatch", methods=["POST"])
def inv_dispatch():
    """Dispatch using visual_servo_node (ArUco-guided pick-and-place)."""
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not ready"}), 503
    data = flask_request.get_json(silent=True) or {}
    mode = data.get("mode", "FIFO").upper()
    if mode not in ("FIFO", "FEFO", "RL"):
        return jsonify({"success": False, "message": "Invalid mode"}), 400

    ok, result = ros_node.dispatch_via_visual_servo(mode)
    return jsonify({
        "success":     ok,
        "message":     result.get("msg", ""),
        "item_name":   result.get("item_name", ""),
        "slot_number": result.get("slot", -1),
        "expiry":      result.get("expiry", ""),
        "rl_reward":   result.get("rl_reward"),
    }), (200 if ok else 503)


@app.route("/inventory/add_item", methods=["POST"])
def inv_add_item():
    """
    Add item.  Accepts either:
      - expiry_ts  (Unix timestamp string, legacy)
      - shelf_life_days  (positive float; expiry = now + shelf_life_days * 86400)
    """
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not ready"}), 503
    data = flask_request.get_json(silent=True) or {}
    name = data.get("item_name", "").strip()
    slot = int(data.get("slot", 0))
    if not name:
        return jsonify({"success": False, "message": "item_name required"}), 400

    # Compute expiry_ts
    expiry_ts: Optional[float] = None
    if data.get("shelf_life_days"):
        try:
            expiry_ts = time.time() + float(data["shelf_life_days"]) * 86400
        except ValueError:
            pass
    elif data.get("expiry_ts"):
        try:
            expiry_ts = float(data["expiry_ts"])
        except ValueError:
            pass

    if not _INV_AVAILABLE:
        return jsonify({"success": False, "message": "Inventory module not installed"}), 500

    try:
        item_id = db_add_item(name, slot, expiry_ts)
        sl = round((expiry_ts - time.time()) / 86400, 1) if expiry_ts else None
        sl_str = f" · shelf life {sl}d" if sl else ""
        return jsonify({"success": True,
                        "message": f"Added '{name}' to slot {slot}{sl_str}",
                        "item_id": item_id})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/inventory/clear", methods=["POST"])
def inv_clear():
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not ready"}), 503
    if _INV_AVAILABLE:
        clear_all()
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Inventory not installed"}), 500


@app.route("/inventory/state")
def inv_state():
    """Full inventory state including shelf-life fields."""
    try:
        if ros_node is None:
            return jsonify({"success": False, "message": "ROS node not ready"}), 503
        if not _INV_AVAILABLE:
            return jsonify({
                "stock_count": 0, "low_stock": False,
                "items": [], "dispatch_log": [],
                "forecast": None,
                "urgency": {"items": [], "summary": {}, "overall": {"status": "OK"}},
            })

        stock = get_stock()
        log   = get_dispatch_log(10)

        items_list = [_item_row(r) for r in stock]

        # Forecast
        forecast = None
        if ros_node.forecaster:
            try:
                ros_node.forecaster.train()
                forecast = ros_node.forecaster.reorder_recommendation()
            except Exception:
                pass

        urgency = ros_node.urgency_classifier.classify_all(items_list)
        rl_rec  = ros_node.rl_optimizer.get_recommendation(items_list)
        count   = stock_count()

        return jsonify({
            "timestamp":    time.time(),
            "stock_count":  count,
            "low_stock":    count <= 1,
            "items":        items_list,
            "dispatch_log": [{"item_name": r["item_name"], "mode": r["mode"],
                              "slot": r["slot"], "ts": r["ts"]} for r in log],
            "forecast":         forecast,
            "urgency":          urgency,
            "rl_recommendation": rl_rec,
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e),
                        "stock_count": 0, "items": [], "dispatch_log": [],
                        "urgency": {"items": [], "summary": {},
                                    "overall": {"status": "ERROR"}}}), 500


@app.route("/inventory/rl_recommendation")
def inv_rl_recommendation():
    if ros_node is None:
        return jsonify({"action": "HOLD", "reason": "Node not ready"})
    if not _INV_AVAILABLE:
        return jsonify({"action": "HOLD", "reason": "Inventory not available"})
    items = [dict(r) for r in get_stock()]
    return jsonify(ros_node.rl_optimizer.get_recommendation(items))


@app.route("/health")
def health():
    task_ok = (ros_node is not None and ros_node.arm_client is not None
               and ros_node.arm_client.server_is_ready())
    return jsonify({
        "status":             "ok",
        "node_ready":         ros_node is not None,
        "task_server_ready":  task_ok,
        "inventory_ready":    _INV_AVAILABLE,
        "visual_servo_topic": "/visual_servo/pick_request",
        "dispatch_mode":      "visual_servo",
    })


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    global ros_node
    rclpy.init()
    ros_node = WebInterface()
    threading.Thread(target=rclpy.spin, args=(ros_node,), daemon=True).start()
    ros_node.get_logger().info("=" * 60)
    ros_node.get_logger().info("  DEXTER Inventory Dashboard  →  http://localhost:5000")
    ros_node.get_logger().info("  Dispatch mode: visual_servo (/visual_servo/pick_request)")
    ros_node.get_logger().info("=" * 60)
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
