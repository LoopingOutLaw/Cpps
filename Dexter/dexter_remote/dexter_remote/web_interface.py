#!/usr/bin/env python3
"""
web_interface.py - Dexter FEFO/FIFO Inventory Control Dashboard

Dispatch flow:
    Browser → POST /inventory/dispatch → dispatch_via_visual_servo()
           → publishes Int32 to /visual_servo/pick_request
           → visual_servo_node.py does the actual pick-and-place
           → DB marked dispatched immediately (optimistic)

Simulation API (standalone, no ROS needed):
    POST /sim/step          { policy, products, state }
    POST /sim/forecast      { history, products }

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
POST /sim/step                 → One simulation day step
POST /sim/forecast             → Demand forecast for products
"""

from __future__ import annotations

import datetime
import json
import math
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
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from std_msgs.msg import String, Int32

from dexter_remote.simlab import SimLabEngine

try:
    from dexter_msgs.action import DexterTask
    _ACTION_AVAILABLE = True
except ImportError:
    _ACTION_AVAILABLE = False
    DexterTask = None

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
    if ts is None:
        return "—"
    return datetime.datetime.fromtimestamp(ts).strftime("%b %d, %Y")


def _shelf_life_days(arrival_ts: Optional[float], expiry_ts: Optional[float]) -> Optional[float]:
    if arrival_ts and expiry_ts:
        return round((expiry_ts - arrival_ts) / 86400, 1)
    return None


def _item_row(row) -> dict:
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
    ALPHA   = 0.1
    GAMMA   = 0.95
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
        state  = self._get_state(items)
        qv     = self._q(state)
        action = self.choose_action(items, explore=False)
        conf   = min(1.0, 0.5 + abs(qv["FIFO"] - qv["FEFO"]) / 2)
        eb = state[0]
        if eb <= 1:
            urgency, reason = "critical", "Items expiring soon — FEFO recommended"
        elif eb == 2:
            urgency, reason = "warning", "Some items approaching expiry"
        else:
            urgency, reason = "normal", "No urgent expiries — FIFO maintains fairness"
        return {"action": action, "confidence": round(conf, 2),
                "reason": reason, "urgency": urgency,
                "q_values": {k: round(v, 3) for k, v in qv.items()}}

    def calculate_reward(self, item: dict, mode: str) -> float:
        now = time.time()
        reward = 1.0
        if item.get("expiry_ts"):
            d = (item["expiry_ts"] - now) / 86400
            if d <= 0:   reward -= 5.0
            elif d <= 2: reward += 2.0 if mode == "FEFO" else 1.0
            elif d <= 7: reward += 0.5 if mode == "FEFO" else 0.0
        age = (now - item.get("arrival_ts", now)) / 86400
        if age > 3 and mode == "FIFO":
            reward += 0.5
        return reward

    def update(self, state: Tuple, action: str, reward: float, next_state: Tuple):
        with self._lock:
            q  = self._q(state)
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
            c["item_id"]   = item.get("id")
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


# ── Simulation Engine (stateless, called per-step from JS) ────────────────────

DOW_MULT = [0.80, 0.88, 1.00, 1.08, 1.25, 1.50, 1.15]

def _sim_eoq(unit_cost: float, base_demand: float, storage_rate: float = 0.005) -> int:
    D = base_demand * 365
    K = 8.0
    h = unit_cost * storage_rate * 365
    return max(1, round(math.sqrt(2 * D * K / max(h, 0.001))))

def _sim_rop(base_demand: float, demand_std: float, lead_mean: float = 1.8) -> int:
    z = 1.645  # 95% service level
    return max(1, math.ceil(base_demand * lead_mean + z * demand_std * math.sqrt(lead_mean)))

def _sim_demand(base_demand: float, demand_std: float, dow: int, trend: float = 1.0) -> int:
    mult = DOW_MULT[dow % 7] * trend
    spike = random.uniform(1.5, 2.0) if random.random() < 0.05 else 1.0
    raw = base_demand * mult * spike + random.gauss(0, demand_std)
    return max(0, round(raw))

def sim_step_server(req_data: dict) -> dict:
    """
    Stateless simulation step called from the browser.
    Browser sends full state; server computes next state and returns results.
    """
    products  = req_data.get("products", [])
    batches   = req_data.get("batches", {})   # productId -> [{age, qty}]
    pending   = req_data.get("pending", [])   # [{productId, qty, arrivalDay, productName, orderedDay}]
    day       = req_data.get("day", 0)
    dow       = req_data.get("dow", 0)
    policy    = req_data.get("policy", "RL")
    qtable    = req_data.get("qtable", {})    # productId -> state_key -> [q0,q1,q2,q3]
    epsilon   = req_data.get("epsilon", 0.3)
    trend     = req_data.get("trend", {})     # productId -> float

    new_batches  = {p["id"]: [dict(b) for b in batches.get(p["id"], [])] for p in products}
    new_pending  = [dict(o) for o in pending]
    events       = []
    product_results = {}
    total_revenue = total_cost = total_waste = total_stockout = 0.0
    orders_placed = []
    new_qtable   = {k: dict(v) for k, v in qtable.items()}
    new_epsilon  = max(0.05, epsilon * 0.9997)
    new_trend    = dict(trend)

    # ── Receive arrived orders ───────────────────────────────────────────────
    still_pending = []
    for order in new_pending:
        if order["arrivalDay"] <= day:
            pid = order["productId"]
            if pid not in new_batches:
                new_batches[pid] = []
            new_batches[pid].append({"age": 0, "qty": order["qty"]})
            events.append({"icon": "📦", "text": f"Order arrived: {order['qty']}× {order['productName']}"})
        else:
            still_pending.append(order)
    new_pending = still_pending

    for product in products:
        pid = product["id"]
        shelf = product["shelfDays"]
        unit_cost  = product["unitCost"]
        sell_price = product["sellPrice"]
        base_d = product["baseDemand"]
        std_d  = product["demandStd"]
        cold   = product.get("cold", True)
        storage_rate = 0.008 if cold else 0.003

        # Update slow trend (mean-reverting)
        t = new_trend.get(pid, 1.0)
        t += random.gauss(0, 0.015)
        t  = 0.85 * t + 0.15 * 1.0
        t  = max(0.6, min(1.5, t))
        new_trend[pid] = t

        batches_p = new_batches.get(pid, [])

        # Age
        for b in batches_p:
            b["age"] += 1

        # Expire
        fresh, expired = [], []
        for b in batches_p:
            if b["age"] > shelf:
                expired.append(b)
            else:
                fresh.append(b)
        new_batches[pid] = fresh
        waste_units = sum(b["qty"] for b in expired)
        waste_cost  = waste_units * unit_cost * 1.8
        if waste_units > 0:
            events.append({"icon": "⚠️", "text": f"Expired: {waste_units}× {product['name']} (lost £{waste_cost:.2f})"})

        # Stock level + storage cost
        stock_level  = sum(b["qty"] for b in fresh)
        storage_cost = stock_level * unit_cost * storage_rate

        # Demand
        demand = _sim_demand(base_d, std_d, dow, t)

        # Dispatch (FEFO = oldest age last if shelfDays matters; sort by age desc = FIFO, asc = FEFO)
        if policy == "FIFO":
            sorted_b = sorted(new_batches[pid], key=lambda b: -b["age"])
        else:  # FEFO / RL
            sorted_b = sorted(new_batches[pid], key=lambda b: b["age"])  # oldest (closest to expiry) first

        sold = 0
        remaining = demand
        for b in sorted_b:
            if remaining <= 0:
                break
            take = min(remaining, b["qty"])
            b["qty"]  -= take
            sold      += take
            remaining -= take

        new_batches[pid] = [b for b in new_batches[pid] if b["qty"] > 0]

        stockout_units = remaining
        margin = sell_price - unit_cost
        stockout_cost  = stockout_units * margin * 1.2
        revenue        = sold * sell_price
        cogs           = sold * unit_cost

        if stockout_units > 0:
            events.append({"icon": "⚡", "text": f"Stockout: {product['name']} — {stockout_units} units unmet"})

        # RL / policy reorder decision
        current_stock = sum(b["qty"] for b in new_batches[pid])
        eoq_val = _sim_eoq(unit_cost, base_d, storage_rate)
        rop_val = _sim_rop(base_d, std_d)

        has_pending = any(o["productId"] == pid for o in new_pending)
        order_qty = 0
        chosen_action = 0  # HOLD

        if not has_pending:
            if policy == "RL":
                # State encoding
                sb = 0 if current_stock == 0 else (1 if current_stock <= 5 else (2 if current_stock <= 20 else (3 if current_stock <= 50 else 4)))
                eb = 0
                if new_batches[pid]:
                    min_days_left = min(shelf - b["age"] for b in new_batches[pid])
                    eb = (0 if min_days_left <= 0 else 1 if min_days_left <= 1 else 2 if min_days_left <= 3 else 3 if min_days_left <= 7 else 4)
                wb = (0 if dow <= 3 else 1 if dow == 4 else 2 if dow == 5 else 3)
                state_key = f"{sb},{eb},{wb}"

                if pid not in new_qtable:
                    new_qtable[pid] = {}
                if state_key not in new_qtable[pid]:
                    # Init with slight FEFO bias when expiry is urgent
                    new_qtable[pid][state_key] = [0.0, 0.5 if sb <= 1 else 0.0, 0.5, 0.3]
                qvals = new_qtable[pid][state_key]

                if random.random() < new_epsilon:
                    chosen_action = random.randint(0, 3)
                else:
                    chosen_action = qvals.index(max(qvals))

                # Reward for this step
                step_reward = (revenue - waste_cost - stockout_cost - storage_cost - cogs) / max(base_d * sell_price, 1)
                max_next = 0.0  # simple TD(0)
                qvals[chosen_action] += 0.15 * (step_reward + 0.95 * max_next - qvals[chosen_action])
                new_qtable[pid][state_key] = qvals

                order_qty_map = {0: 0, 1: max(1, eoq_val // 2), 2: eoq_val, 3: int(eoq_val * 1.5)}
                order_qty = order_qty_map[chosen_action]

                # Safety override: if below ROP with no pending, always order something
                if current_stock <= rop_val and chosen_action == 0 and not has_pending:
                    order_qty = eoq_val
                    chosen_action = 2

            elif policy in ("FEFO", "FIFO"):
                if current_stock <= rop_val:
                    order_qty = eoq_val
                    chosen_action = 2

        order_cost = 0.0
        if order_qty > 0:
            lead_time = random.choice([1, 1, 2, 2, 3])
            order_cost = 5.0 + 0.15 * order_qty + order_qty * unit_cost
            new_pending.append({
                "productId":   pid,
                "productName": product["name"],
                "qty":         order_qty,
                "orderedDay":  day,
                "arrivalDay":  day + lead_time,
            })
            orders_placed.append({
                "name":      product["name"],
                "qty":       order_qty,
                "leadTime":  lead_time,
                "cost":      round(order_cost, 2),
            })
            events.append({"icon": "🛒", "text": f"Order placed: {order_qty}× {product['name']} (arrives day {day + lead_time})"})

        day_cost   = waste_cost + storage_cost + stockout_cost + cogs + order_cost
        day_profit = revenue - day_cost

        total_revenue  += revenue
        total_cost     += day_cost
        total_waste    += waste_units
        total_stockout += stockout_units

        product_results[pid] = {
            "name":         product["name"],
            "demand":       demand,
            "sold":         sold,
            "stockout":     stockout_units,
            "wasted":       waste_units,
            "revenue":      round(revenue, 2),
            "cost":         round(day_cost, 2),
            "profit":       round(day_profit, 2),
            "currentStock": sum(b["qty"] for b in new_batches[pid]),
            "eoq":          eoq_val,
            "rop":          rop_val,
            "action":       ["HOLD", "ORDER_SMALL", "ORDER_EOQ", "ORDER_SURGE"][chosen_action],
        }

    total_profit = total_revenue - total_cost
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return {
        "day":          day + 1,
        "dow":          dow_names[(dow + 1) % 7],
        "nextDow":      (dow + 1) % 7,
        "batches":      new_batches,
        "pending":      new_pending,
        "qtable":       new_qtable,
        "epsilon":      round(new_epsilon, 4),
        "trend":        new_trend,
        "events":       events,
        "products":     product_results,
        "orders":       orders_placed,
        "totalRevenue": round(total_revenue, 2),
        "totalCost":    round(total_cost, 2),
        "totalProfit":  round(total_profit, 2),
        "totalWaste":   int(total_waste),
        "totalStockout":int(total_stockout),
    }


def sim_forecast_server(req_data: dict) -> dict:
    """
    Return a 14-day demand forecast for all products.
    Uses simple Holt-Winters smoothing if history is provided.
    """
    products = req_data.get("products", [])
    history  = req_data.get("history", [])   # list of day records
    results  = {}

    for product in products:
        pid  = product["id"]
        base = product["baseDemand"]
        std  = product["demandStd"]

        # Build demand series from history
        series = []
        for day_rec in history:
            pr = day_rec.get("products", {}).get(pid, {})
            if "demand" in pr:
                series.append(pr["demand"])

        # Holt-Winters double exp smoothing
        α, β = 0.3, 0.1
        if len(series) >= 2:
            L, T = float(series[0]), float(series[1]) - float(series[0])
            for obs in series[1:]:
                Ln = α * obs + (1 - α) * (L + T)
                Tn = β * (Ln - L) + (1 - β) * T
                L, T = Ln, Tn
        else:
            L, T = float(base), 0.0

        # Build 14-day forecast
        forecast = []
        import datetime as dt
        for h in range(1, 15):
            mu    = max(0.0, L + h * T)
            sigma = max(std * (1 + 0.06 * h), 0.5)
            dname = dt.date.today() + dt.timedelta(days=h)
            dow   = dname.weekday()
            mu   *= DOW_MULT[dow]
            forecast.append({
                "day":      h,
                "date":     dname.strftime("%a %d %b"),
                "forecast": round(mu, 1),
                "lo80":     round(max(0, mu - 1.282 * sigma), 1),
                "hi80":     round(mu + 1.282 * sigma, 1),
                "lo95":     round(max(0, mu - 1.960 * sigma), 1),
                "hi95":     round(mu + 1.960 * sigma, 1),
            })
        results[pid] = {
            "product":   product["name"],
            "hw_level":  round(L, 2),
            "hw_trend":  round(T, 3),
            "forecast":  forecast,
            "eoq":       _sim_eoq(product["unitCost"], base),
            "rop":       _sim_rop(base, std),
        }

    return results


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

        # ── Visual servo publisher ────────────────────────────────────────────
        # Reliable QoS so messages are NOT dropped even during brief disconnects.
        qos = QoSProfile(
            depth=10,
            reliability=QoSReliabilityPolicy.RELIABLE,
        )
        self.pick_pub = self.create_publisher(Int32, "/visual_servo/pick_request", qos)
        self.get_logger().info("Publisher created: /visual_servo/pick_request (RELIABLE QoS)")

        # Subscribe to servo status for health reporting
        self._servo_state = "unknown"
        self.create_subscription(String, "/visual_servo/status", self._servo_status_cb, 10)

        # Inventory — seed defaults so there are always items in DB
        if _INV_AVAILABLE:
            init_db()
            preserve_db = os.environ.get("DEXTER_PRESERVE_DB", "0") == "1"
            if preserve_db:
                self.get_logger().info(f"DB preserved (DEXTER_PRESERVE_DB=1). Current stock: {stock_count()}")
            else:
                self.get_logger().info("Resetting DB to default items on startup.")
                try:
                    reset_with_defaults()
                except Exception as e:
                    self.get_logger().warning(f"reset_with_defaults failed: {e}")
            self.forecaster = DemandForecaster()
        else:
            self.get_logger().warn("dexter_inventory not available.")
            self.forecaster = None

        self.rl_optimizer       = RLDispatchOptimizer()
        self.urgency_classifier = UrgencyClassifier()

        self.get_logger().info("WebInterface ready  →  http://localhost:5000")

    def _servo_status_cb(self, msg: String):
        self._servo_state = msg.data[:80]

    # ── Arm task ──────────────────────────────────────────────────────────────

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
                    result_holder.update({"ok": r.result.success, "msg": f"{name} complete"})
                except Exception as e:
                    result_holder.update({"ok": False, "msg": str(e)})
                finally:
                    done.set()

            self.arm_client.send_goal_async(goal).add_done_callback(_goal_cb)
            done.wait(timeout=30.0)
            return result_holder.get("ok", False), result_holder.get("msg", "Timeout")
        finally:
            self._lock.release()

    # ── Dispatch via visual servo ─────────────────────────────────────────────

    def dispatch_via_visual_servo(self, mode: str) -> Tuple[bool, dict]:
        """
        Select next item (FIFO/FEFO/RL), publish slot to /visual_servo/pick_request,
        mark dispatched in DB.  The visual_servo_node executes the full pick sequence.
        """
        if not _INV_AVAILABLE:
            return False, {"msg": "Inventory module not available"}

        actual_mode = mode
        if mode == "RL":
            try:
                items   = [dict(r) for r in get_stock()]
                rec     = self.rl_optimizer.get_recommendation(items)
                actual_mode = rec["action"] if rec["action"] != "HOLD" else "FIFO"
            except Exception:
                actual_mode = "FIFO"

        try:
            item_row = get_fefo_item() if actual_mode == "FEFO" else get_fifo_item()
        except Exception as e:
            return False, {"msg": f"DB error: {e}"}

        if item_row is None:
            return False, {"msg": "No items in stock to dispatch. Add items or run: ros2 run dexter_inventory seed_data --clear"}

        item = dict(item_row)
        slot = item["slot"]

        # Publish pick request to visual_servo_node
        try:
            msg      = Int32()
            msg.data = slot
            self.pick_pub.publish(msg)
            self.get_logger().info(
                f"[dispatch] ▶ /visual_servo/pick_request  slot={slot}  "
                f"item='{item['name']}'  mode={actual_mode}")
        except Exception as e:
            self.get_logger().error(f"Publisher error: {e}")
            return False, {"msg": f"Failed to publish pick request: {e}"}

        # Update DB and RL table
        reward = 0.0
        try:
            pre_items  = [dict(r) for r in get_stock()]
            pre_state  = self.rl_optimizer._get_state(pre_items)
            reward     = self.rl_optimizer.calculate_reward(item, actual_mode)
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
simlab_engine = SimLabEngine(seed=42)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/task", methods=["POST"])
def handle_task():
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not ready"}), 503
    data     = flask_request.get_json(silent=True) or {}
    task_num = data.get("task_number")
    if task_num is None:
        return jsonify({"success": False, "message": "Missing task_number"}), 400
    ok, msg = ros_node.send_task(int(task_num))
    return jsonify({"success": ok, "message": msg}), (200 if ok else 503)


@app.route("/inventory/dispatch", methods=["POST"])
def inv_dispatch():
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
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not ready"}), 503
    data = flask_request.get_json(silent=True) or {}
    name = data.get("item_name", "").strip()
    slot = int(data.get("slot", 0))
    if not name:
        return jsonify({"success": False, "message": "item_name required"}), 400

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


@app.route("/inventory/reset_defaults", methods=["POST"])
def inv_reset_defaults():
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not ready"}), 503
    if not _INV_AVAILABLE:
        return jsonify({"success": False, "message": "Inventory module not installed"}), 500
    try:
        reset_with_defaults()
        return jsonify({"success": True, "message": "Inventory reset to defaults"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/inventory/state")
def inv_state():
    try:
        if ros_node is None:
            return jsonify({"success": False, "message": "ROS node not ready"}), 503
        if not _INV_AVAILABLE:
            return jsonify({
                "stock_count": 0, "low_stock": False,
                "items": [], "dispatch_log": [],
                "forecast": None,
                "urgency": {"items": [], "summary": {}, "overall": {"status": "OK"}},
                "rl_recommendation": {"action": "HOLD", "reason": "Inventory unavailable"},
            })

        stock = get_stock()
        log   = get_dispatch_log(10)
        items_list = [_item_row(r) for r in stock]

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
            "timestamp":         time.time(),
            "stock_count":       count,
            "low_stock":         count <= 1,
            "items":             items_list,
            "dispatch_log":      [{"item_name": r["item_name"], "mode": r["mode"],
                                   "slot": r["slot"], "ts": r["ts"]} for r in log],
            "forecast":          forecast,
            "urgency":           urgency,
            "rl_recommendation": rl_rec,
            "servo_state":       ros_node._servo_state,
        })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False, "message": str(e),
            "stock_count": 0, "items": [], "dispatch_log": [],
            "urgency": {"items": [], "summary": {},
                        "overall": {"status": "ERROR", "message": str(e)}},
            "rl_recommendation": {"action": "HOLD", "reason": "Error"},
        }), 500


@app.route("/inventory/rl_recommendation")
def inv_rl_recommendation():
    if ros_node is None:
        return jsonify({"action": "HOLD", "reason": "Node not ready"})
    if not _INV_AVAILABLE:
        return jsonify({"action": "HOLD", "reason": "Inventory not available"})
    items = [dict(r) for r in get_stock()]
    return jsonify(ros_node.rl_optimizer.get_recommendation(items))


# ── Simulation routes (stateless — browser owns the state) ────────────────────

@app.route("/sim/step", methods=["POST"])
def sim_step():
    """One day simulation step. Browser sends full state, server returns next state."""
    try:
        data   = flask_request.get_json(silent=True) or {}
        result = sim_step_server(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sim/forecast", methods=["POST"])
def sim_forecast():
    """14-day demand forecast for the simulation products."""
    try:
        data   = flask_request.get_json(silent=True) or {}
        result = sim_forecast_server(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Persistent SimLab routes (server-owned RL environment) ───────────────────

@app.route("/simlab")
def simlab_page():
    return render_template("simlab.html")


@app.route("/simlab/state")
def simlab_state():
    return jsonify(simlab_engine.state())


@app.route("/simlab/reset", methods=["POST"])
def simlab_reset():
    data = flask_request.get_json(silent=True) or {}
    cfg = data.get("config", None)
    if cfg is not None and not isinstance(cfg, dict):
        return jsonify({"success": False, "message": "config must be an object"}), 400
    simlab_engine.reset(cfg)
    return jsonify({"success": True, "state": simlab_engine.state()})


@app.route("/simlab/train", methods=["POST"])
def simlab_train():
    data = flask_request.get_json(silent=True) or {}
    episodes = int(data.get("episodes", 140))
    episode_days = int(data.get("episode_days", 35))
    result = simlab_engine.train(episodes=episodes, episode_days=episode_days)
    return jsonify({"success": True, "train": result, "state": simlab_engine.state()})


@app.route("/simlab/run", methods=["POST"])
def simlab_run():
    data = flask_request.get_json(silent=True) or {}
    days = int(data.get("days", 1))
    use_rl = bool(data.get("use_rl", True))
    forced_order_raw = data.get("forced_order", None)
    forced_order = None
    if forced_order_raw is not None and str(forced_order_raw) != "":
        forced_order = int(forced_order_raw)
    result = simlab_engine.run_days(days=days, use_rl=use_rl, forced_order=forced_order)
    return jsonify({"success": True, **result})


@app.route("/simlab/forecast")
def simlab_forecast():
    days = int(flask_request.args.get("days", "14"))
    samples = int(flask_request.args.get("samples", "200"))
    return jsonify(simlab_engine.forecast(horizon_days=days, samples=samples))


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
        "servo_state":        ros_node._servo_state if ros_node else "node_not_ready",
        "dispatch_mode":      "visual_servo",
    })


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    global ros_node
    rclpy.init()
    ros_node = WebInterface()
    threading.Thread(target=rclpy.spin, args=(ros_node,), daemon=True).start()
    ros_node.get_logger().info("=" * 64)
    ros_node.get_logger().info("  DEXTER Inventory Dashboard  →  http://localhost:5000")
    ros_node.get_logger().info("  Dispatch: /visual_servo/pick_request (RELIABLE QoS)")
    ros_node.get_logger().info("  Seed DB : ros2 run dexter_inventory seed_data --clear")
    ros_node.get_logger().info("=" * 64)
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
