#!/usr/bin/env python3
"""
standalone_dashboard.py
Run the inventory dashboard without ROS2 for quick testing.

Usage:
    python3 standalone_dashboard.py

Then open http://localhost:5000
"""

import os
import sys
import time
import json
import random
import threading
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from flask import Flask, render_template, jsonify, request as flask_request

# Add package to path
pkg_dir = Path(__file__).parent
sys.path.insert(0, str(pkg_dir.parent))

from dexter_inventory.inventory_db import (
    init_db, get_stock, get_dispatch_log,
    stock_count, clear_all, add_item as db_add_item,
    get_fifo_item, get_fefo_item, mark_dispatched,
)
from dexter_inventory.dispatch_engine import format_expiry
from dexter_inventory.ml_forecast import DemandForecaster


# ==============================================================================
# RL Optimizer (simplified version)
# ==============================================================================

class RLDispatchOptimizer:
    ACTIONS = ["FIFO", "FEFO", "HOLD"]
    
    def __init__(self):
        self.q_table: Dict[Tuple, Dict[str, float]] = {}
        
    def _get_state(self, items: List[dict]) -> Tuple:
        if not items:
            return (0, 0, 0)
        
        now = time.time()
        min_expiry_days = float('inf')
        for item in items:
            if item.get("expiry_ts"):
                days = (item["expiry_ts"] - now) / 86400
                min_expiry_days = min(min_expiry_days, days)
        
        if min_expiry_days == float('inf'):
            expiry_bucket = 3
        elif min_expiry_days <= 0:
            expiry_bucket = 0
        elif min_expiry_days <= 2:
            expiry_bucket = 1
        elif min_expiry_days <= 7:
            expiry_bucket = 2
        else:
            expiry_bucket = 3
        
        count = len(items)
        stock_bucket = 0 if count == 0 else (1 if count <= 1 else (2 if count <= 3 else 3))
        
        return (expiry_bucket, stock_bucket, 1)
    
    def get_recommendation(self, items: List[dict]) -> Dict:
        if not items:
            return {"action": "HOLD", "confidence": 1.0, "reason": "No items in stock", "urgency": "none"}
        
        state = self._get_state(items)
        expiry_bucket = state[0]
        
        if expiry_bucket <= 1:
            action, urgency = "FEFO", "critical"
            reason = "Items expiring soon - FEFO recommended"
        elif expiry_bucket == 2:
            action, urgency = "FEFO", "warning"
            reason = "Some items approaching expiry"
        else:
            action, urgency = "FIFO", "normal"
            reason = "No urgent expiries - FIFO maintains fairness"
        
        return {"action": action, "confidence": 0.85, "reason": reason, "urgency": urgency, "q_values": {}, "state": {}}


# ==============================================================================
# Urgency Classifier
# ==============================================================================

class UrgencyClassifier:
    @staticmethod
    def classify(item: dict) -> Dict:
        now = time.time()
        result = {"level": "LOW", "color": "#3fb950", "priority": 4, "reason": "No expiry set", "days_remaining": None}
        
        if not item.get("expiry_ts"):
            return result
        
        days_remaining = (item["expiry_ts"] - now) / 86400
        result["days_remaining"] = round(days_remaining, 1)
        
        if days_remaining <= 0:
            result.update({"level": "CRITICAL", "color": "#f85149", "priority": 1, "reason": "EXPIRED"})
        elif days_remaining <= 2:
            result.update({"level": "HIGH", "color": "#d29922", "priority": 2, "reason": f"Expiring in {days_remaining:.1f} days"})
        elif days_remaining <= 7:
            result.update({"level": "MEDIUM", "color": "#58a6ff", "priority": 3, "reason": f"Expiring in {days_remaining:.1f} days"})
        else:
            result["reason"] = f"{days_remaining:.0f} days until expiry"
        
        return result
    
    @staticmethod
    def classify_all(items: List[dict]) -> Dict:
        classified, summary = [], {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for item in items:
            c = UrgencyClassifier.classify(item)
            c["item_id"], c["item_name"] = item.get("id"), item.get("name")
            classified.append(c)
            summary[c["level"]] += 1
        
        classified.sort(key=lambda x: x["priority"])
        
        if summary["CRITICAL"] > 0:
            overall = {"status": "CRITICAL", "message": f"{summary['CRITICAL']} item(s) expired!"}
        elif summary["HIGH"] > 0:
            overall = {"status": "WARNING", "message": f"{summary['HIGH']} item(s) expiring soon"}
        else:
            overall = {"status": "OK", "message": "All items within safe expiry range"}
        
        return {"items": classified, "summary": summary, "overall": overall}


# ==============================================================================
# RFID Simulator
# ==============================================================================

class RFIDSimulator:
    def __init__(self):
        self._tags, self._scan_history = {}, []
    
    def generate_tag(self) -> str:
        return f"RFID-{random.randint(1000000000, 9999999999):010d}"
    
    def register_tag(self, tag_id: str, item_data: dict):
        self._tags[tag_id] = {"tag_id": tag_id, **item_data}
    
    def scan_tag(self, tag_id: str):
        self._scan_history.append({"tag_id": tag_id, "timestamp": time.time(), "found": tag_id in self._tags})
        self._scan_history = self._scan_history[-50:]
        return self._tags.get(tag_id)
    
    def get_scan_history(self, limit: int = 10):
        return list(reversed(self._scan_history[-limit:]))


# ==============================================================================
# Flask App
# ==============================================================================

def _find_template_dir() -> str:
    for path in [pkg_dir.parent / "templates", pkg_dir / ".." / "templates", Path.cwd() / "templates"]:
        if path.exists():
            return str(path.resolve())
    return str(pkg_dir.parent / "templates")


app = Flask(__name__, template_folder=_find_template_dir())
init_db()
forecaster = DemandForecaster()
rl_optimizer = RLDispatchOptimizer()
rfid_simulator = RFIDSimulator()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/task", methods=["POST"])
def handle_task():
    data = flask_request.get_json(silent=True) or {}
    task = data.get("task_number", 0)
    names = {0: "Home", 1: "Pick", 2: "Sleep"}
    return jsonify({"success": True, "message": f"{names.get(task, 'Task')} simulated (no ROS)"})


@app.route("/inventory/dispatch", methods=["POST"])
def inv_dispatch():
    data = flask_request.get_json(silent=True) or {}
    mode = data.get("mode", "FIFO").upper()
    
    if mode == "RL":
        stock = get_stock()
        items = [dict(row) for row in stock]
        rec = rl_optimizer.get_recommendation(items)
        mode = rec["action"]
    
    item = get_fifo_item() if mode == "FIFO" else get_fefo_item()
    
    if not item:
        return jsonify({"success": False, "message": "No items in stock"}), 200
    
    mark_dispatched(item["id"], mode)
    
    return jsonify({
        "success": True,
        "message": f"Dispatched '{item['name']}' from slot {item['slot']} ({mode})",
        "item_name": item["name"],
        "slot_number": item["slot"],
        "expiry": format_expiry(item["expiry_ts"]),
        "rl_reward": 1.0
    })


@app.route("/inventory/add_item", methods=["POST"])
def inv_add_item():
    data = flask_request.get_json(silent=True) or {}
    name = data.get("item_name", "").strip()
    slot = int(data.get("slot", 0))
    expiry = data.get("expiry_ts", "")
    
    if not name:
        return jsonify({"success": False, "message": "item_name required"}), 400
    
    try:
        expiry_ts = float(expiry) if expiry else None
        item_id = db_add_item(name, slot, expiry_ts)
        rfid_tag = rfid_simulator.generate_tag()
        rfid_simulator.register_tag(rfid_tag, {"item_id": item_id, "name": name, "slot": slot})
        return jsonify({"success": True, "message": f"Added '{name}' to slot {slot} [RFID: {rfid_tag}]"})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/inventory/rfid_scan", methods=["POST"])
def inv_rfid_scan():
    data = flask_request.get_json(silent=True) or {}
    tag_id = data.get("rfid_tag") or rfid_simulator.generate_tag()
    item_data = rfid_simulator.scan_tag(tag_id)
    return jsonify({"success": True, "tag_id": tag_id, "found": item_data is not None, "item": item_data, "timestamp": time.time()})


@app.route("/inventory/clear", methods=["POST"])
def inv_clear():
    clear_all()
    rfid_simulator._tags.clear()
    return jsonify({"success": True})


@app.route("/inventory/state")
def inv_state():
    stock = get_stock()
    log = get_dispatch_log(10)
    
    items_list = [{"id": r["id"], "name": r["name"], "slot": r["slot"], "arrival_ts": r["arrival_ts"], "expiry_ts": r["expiry_ts"], "expiry": format_expiry(r["expiry_ts"])} for r in stock]
    
    forecaster.train()
    forecast = forecaster.reorder_recommendation()
    urgency = UrgencyClassifier.classify_all(items_list)
    rl_rec = rl_optimizer.get_recommendation(items_list)
    
    return jsonify({
        "timestamp": time.time(),
        "stock_count": stock_count(),
        "low_stock": stock_count() <= 1,
        "items": items_list,
        "dispatch_log": [{"item_name": r["item_name"], "mode": r["mode"], "slot": r["slot"], "ts": r["ts"]} for r in log],
        "forecast": forecast,
        "urgency": urgency,
        "rl_recommendation": rl_rec,
        "rfid_scans": rfid_simulator.get_scan_history(5)
    })


@app.route("/inventory/rl_recommendation")
def inv_rl_recommendation():
    stock = get_stock()
    items = [dict(row) for row in stock]
    return jsonify(rl_optimizer.get_recommendation(items))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "task_server_ready": False, "inventory_ready": True, "services_ready": False, "mode": "standalone"})


if __name__ == "__main__":
    print("=" * 60)
    print("  DEXTER FEFO/FIFO Inventory Dashboard (Standalone Mode)")
    print("=" * 60)
    print(f"  Template dir: {_find_template_dir()}")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
