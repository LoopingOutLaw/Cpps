#!/usr/bin/env python3
"""
web_interface.py - Dexter FEFO/FIFO Inventory Control Dashboard

A comprehensive inventory management system featuring:
- RFID tag simulation with arrival timestamps
- FIFO (First-In-First-Out) dispatch mode
- FEFO (First-Expiry-First-Out) dispatch mode  
- RL-based dispatch optimization
- Real-time shelf visualization
- Voice command support
- ML-powered demand forecasting
- Urgency classification for perishable items

Runs on port 5000: http://localhost:5000

Routes
------
GET  /                         -> Dashboard (index.html)
POST /task                     { task_number: 0|1|2 } -> Arm control
POST /inventory/dispatch       { mode: "FIFO"|"FEFO"|"RL" } -> Dispatch item
POST /inventory/add_item       { item_name, slot, expiry_ts, rfid_tag }
POST /inventory/rfid_scan      { rfid_tag } -> Simulate RFID scan
POST /inventory/clear          -> Wipe database
GET  /inventory/state          -> JSON stock + forecast + urgency
GET  /inventory/rl_recommendation -> Get RL dispatch suggestion
GET  /health                   -> Health check
"""

from __future__ import annotations

import os
import sys
import time
import json
import random
import threading
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

from flask import Flask, render_template, jsonify, request as flask_request

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient  # type: ignore[attr-defined]
from rclpy.qos import QoSProfile, ReliabilityPolicy

# ROS2 message imports - these are generated at build time
try:
    from dexter_msgs.action import DexterTask  # type: ignore[import]
    _ACTION_AVAILABLE = True
except ImportError:
    _ACTION_AVAILABLE = False
    DexterTask = None  # type: ignore[assignment,misc]

# Inventory services (imported if package is installed)
try:
    from dexter_msgs.srv import DispatchItem, AddItem as AddItemSrv  # type: ignore[import]
    _SRV_AVAILABLE = True
except ImportError:
    _SRV_AVAILABLE = False
    DispatchItem = None  # type: ignore[assignment,misc]
    AddItemSrv = None  # type: ignore[assignment,misc]

# Inventory database and logic
try:
    from dexter_inventory.inventory_db import (  # type: ignore[import]
        init_db, get_stock, get_dispatch_log,
        stock_count, clear_all, add_item as db_add_item,
    )
    from dexter_inventory.dispatch_engine import format_expiry  # type: ignore[import]
    from dexter_inventory.ml_forecast import DemandForecaster  # type: ignore[import]
    _INV_AVAILABLE = True
except ImportError:
    _INV_AVAILABLE = False
    
    # Provide stubs when inventory module is not available
    def init_db() -> None: pass
    def get_stock() -> list: return []
    def get_dispatch_log(limit: int = 10) -> list: return []
    def stock_count() -> int: return 0
    def clear_all() -> None: pass
    def db_add_item(name: str, slot: int, expiry: Any = None) -> str: return ""
    def format_expiry(ts: Any) -> str: return "N/A"
    
    class DemandForecaster:  # type: ignore[no-redef]
        def train(self) -> bool: return False
        def reorder_recommendation(self) -> dict: 
            return {"reorder": False, "predicted_demand": 0, "current_stock": 0, "order_quantity": 0, "reason": "N/A"}


# ==============================================================================
# RL-Based Dispatch Optimizer
# ==============================================================================

class RLDispatchOptimizer:
    """
    Reinforcement Learning based dispatch optimizer.
    
    Uses a simple Q-learning approach to learn optimal dispatch sequences
    that minimize:
    - Spoilage (expired items)
    - Shortages (running out of high-demand items)
    - Waiting time (FIFO fairness)
    
    State: (days_to_expiry_bucket, stock_level_bucket, demand_bucket)
    Actions: FIFO, FEFO, or hold
    """
    
    ACTIONS = ["FIFO", "FEFO", "HOLD"]
    ALPHA = 0.1      # Learning rate
    GAMMA = 0.95     # Discount factor
    EPSILON = 0.1    # Exploration rate
    
    def __init__(self):
        self.q_table: Dict[Tuple, Dict[str, float]] = {}
        self.episode_rewards: List[float] = []
        self._lock = threading.Lock()
        
    def _get_state(self, items: List[dict]) -> Tuple:
        """Convert inventory state to discrete state tuple."""
        if not items:
            return (0, 0, 0)
        
        now = time.time()
        
        # Min days to expiry (bucket: 0=expired, 1=urgent<2d, 2=soon<7d, 3=ok)
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
        
        # Stock level bucket (0=empty, 1=low, 2=medium, 3=high)
        count = len(items)
        if count == 0:
            stock_bucket = 0
        elif count <= 1:
            stock_bucket = 1
        elif count <= 3:
            stock_bucket = 2
        else:
            stock_bucket = 3
        
        # Demand bucket (based on recent dispatch rate)
        demand_bucket = 1  # Default medium
        
        return (expiry_bucket, stock_bucket, demand_bucket)
    
    def _get_q_values(self, state: Tuple) -> Dict[str, float]:
        """Get Q-values for a state, initializing if needed."""
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.ACTIONS}
        return self.q_table[state]
    
    def choose_action(self, items: List[dict], explore: bool = True) -> str:
        """Choose dispatch action using epsilon-greedy policy."""
        if not items:
            return "HOLD"
        
        state = self._get_state(items)
        q_values = self._get_q_values(state)
        
        # Epsilon-greedy exploration
        if explore and random.random() < self.EPSILON:
            return random.choice(self.ACTIONS[:2])  # FIFO or FEFO
        
        # Pick best action (excluding HOLD if items present)
        best_action = max(self.ACTIONS[:2], key=lambda a: q_values[a])
        return best_action
    
    def get_recommendation(self, items: List[dict]) -> Dict:
        """Get RL recommendation with explanation."""
        if not items:
            return {
                "action": "HOLD",
                "confidence": 1.0,
                "reason": "No items in stock",
                "urgency": "none"
            }
        
        state = self._get_state(items)
        q_values = self._get_q_values(state)
        
        # Determine best action
        action = self.choose_action(items, explore=False)
        
        # Calculate confidence from Q-value difference
        q_diff = abs(q_values["FIFO"] - q_values["FEFO"])
        confidence = min(1.0, 0.5 + q_diff / 2)
        
        # Generate explanation
        expiry_bucket, stock_bucket, _ = state
        
        if expiry_bucket <= 1:
            urgency = "critical"
            reason = "Items expiring soon - FEFO recommended to prevent spoilage"
        elif expiry_bucket == 2:
            urgency = "warning"
            reason = "Some items approaching expiry - consider FEFO"
        else:
            urgency = "normal"
            reason = "No urgent expiries - FIFO maintains fairness"
        
        return {
            "action": action,
            "confidence": round(confidence, 2),
            "reason": reason,
            "urgency": urgency,
            "q_values": {k: round(v, 3) for k, v in q_values.items()},
            "state": {"expiry_bucket": expiry_bucket, "stock_bucket": stock_bucket}
        }
    
    def update(self, state: Tuple, action: str, reward: float, next_state: Tuple):
        """Update Q-values using Q-learning update rule."""
        with self._lock:
            q_values = self._get_q_values(state)
            next_q_values = self._get_q_values(next_state)
            
            max_next_q = max(next_q_values.values())
            q_values[action] += self.ALPHA * (
                reward + self.GAMMA * max_next_q - q_values[action]
            )
            
            self.episode_rewards.append(reward)
    
    def calculate_reward(self, item: dict, mode: str) -> float:
        """Calculate reward for dispatching an item with given mode."""
        now = time.time()
        reward = 1.0  # Base reward for successful dispatch
        
        if item.get("expiry_ts"):
            days_to_expiry = (item["expiry_ts"] - now) / 86400
            
            if days_to_expiry <= 0:
                # Expired - big penalty
                reward -= 5.0
            elif days_to_expiry <= 2:
                # Urgent - bonus for dispatching
                reward += 2.0 if mode == "FEFO" else 1.0
            elif days_to_expiry <= 7:
                # Warning - small bonus for FEFO
                reward += 0.5 if mode == "FEFO" else 0.0
        
        # FIFO bonus for fairness
        arrival_age = (now - item["arrival_ts"]) / 86400
        if arrival_age > 3 and mode == "FIFO":
            reward += 0.5
        
        return reward


# ==============================================================================
# Urgency Classifier
# ==============================================================================

class UrgencyClassifier:
    """
    Classifies items by dispatch urgency based on expiry and arrival time.
    
    Urgency levels:
    - CRITICAL: Expired or expiring today
    - HIGH: Expiring within 2 days
    - MEDIUM: Expiring within 7 days
    - LOW: No expiry or > 7 days
    """
    
    LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    
    @staticmethod
    def classify(item: dict) -> Dict:
        """Classify a single item's urgency."""
        now = time.time()
        result = {
            "level": "LOW",
            "color": "#3fb950",  # Green
            "priority": 4,
            "reason": "No expiry set",
            "days_remaining": None
        }
        
        if not item.get("expiry_ts"):
            return result
        
        days_remaining = (item["expiry_ts"] - now) / 86400
        result["days_remaining"] = round(days_remaining, 1)
        
        if days_remaining <= 0:
            result.update({
                "level": "CRITICAL",
                "color": "#f85149",  # Red
                "priority": 1,
                "reason": "EXPIRED - dispatch immediately"
            })
        elif days_remaining <= 2:
            result.update({
                "level": "HIGH", 
                "color": "#d29922",  # Orange
                "priority": 2,
                "reason": f"Expiring in {days_remaining:.1f} days"
            })
        elif days_remaining <= 7:
            result.update({
                "level": "MEDIUM",
                "color": "#58a6ff",  # Blue
                "priority": 3,
                "reason": f"Expiring in {days_remaining:.1f} days"
            })
        else:
            result["reason"] = f"{days_remaining:.0f} days until expiry"
        
        return result
    
    @staticmethod
    def classify_all(items: List[dict]) -> Dict:
        """Classify all items and provide summary."""
        classified = []
        summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for item in items:
            classification = UrgencyClassifier.classify(item)
            classification["item_id"] = item.get("id")
            classification["item_name"] = item.get("name")
            classified.append(classification)
            summary[classification["level"]] += 1
        
        # Sort by priority (critical first)
        classified.sort(key=lambda x: x["priority"])
        
        # Overall status
        if summary["CRITICAL"] > 0:
            overall = {"status": "CRITICAL", "message": f"{summary['CRITICAL']} item(s) expired!"}
        elif summary["HIGH"] > 0:
            overall = {"status": "WARNING", "message": f"{summary['HIGH']} item(s) expiring soon"}
        else:
            overall = {"status": "OK", "message": "All items within safe expiry range"}
        
        return {
            "items": classified,
            "summary": summary,
            "overall": overall
        }


# ==============================================================================
# RFID Simulator
# ==============================================================================

class RFIDSimulator:
    """
    Simulates RFID tag scanning for inventory items.
    
    In a real system, this would interface with actual RFID hardware
    (e.g., MFRC522 reader on Raspberry Pi).
    """
    
    def __init__(self):
        self._tags: Dict[str, dict] = {}
        self._scan_history: List[dict] = []
        self._lock = threading.Lock()
    
    def generate_tag(self) -> str:
        """Generate a simulated RFID tag ID."""
        return f"RFID-{random.randint(1000000000, 9999999999):010d}"
    
    def register_tag(self, tag_id: str, item_data: dict) -> None:
        """Register a tag with item data."""
        with self._lock:
            self._tags[tag_id] = {
                "tag_id": tag_id,
                "item_name": item_data.get("name", "Unknown"),
                "registered_at": time.time(),
                **item_data
            }
    
    def scan_tag(self, tag_id: str) -> Optional[dict]:
        """Simulate scanning an RFID tag."""
        with self._lock:
            scan_record = {
                "tag_id": tag_id,
                "timestamp": time.time(),
                "found": tag_id in self._tags
            }
            self._scan_history.append(scan_record)
            
            # Keep only last 50 scans
            if len(self._scan_history) > 50:
                self._scan_history = self._scan_history[-50:]
            
            if tag_id in self._tags:
                return self._tags[tag_id].copy()
            return None
    
    def get_scan_history(self, limit: int = 10) -> List[dict]:
        """Get recent scan history."""
        with self._lock:
            return list(reversed(self._scan_history[-limit:]))
    
    def unregister_tag(self, tag_id: str) -> bool:
        """Remove a tag from the registry (e.g., after dispatch)."""
        with self._lock:
            if tag_id in self._tags:
                del self._tags[tag_id]
                return True
            return False


# ==============================================================================
# Web Interface ROS Node
# ==============================================================================

class WebInterface(Node):
    """ROS2 Node that provides web dashboard for inventory control."""
    
    TASK_NAMES = {0: "Home/Wake", 1: "Pick", 2: "Sleep"}
    
    def __init__(self):
        super().__init__("web_interface")
        self._lock = threading.Lock()
        
        # Action client for arm control
        self.arm_client = ActionClient(self, DexterTask, "task_server")
        
        # Service clients for inventory
        if _SRV_AVAILABLE:
            self.dispatch_client = self.create_client(
                DispatchItem, "inventory/dispatch"
            )
            self.add_item_client = self.create_client(
                AddItemSrv, "inventory/add_item"
            )
        else:
            self.dispatch_client = None
            self.add_item_client = None
        
        # Initialize subsystems
        if _INV_AVAILABLE:
            init_db()
            self.forecaster = DemandForecaster()
        else:
            self.forecaster = None
        
        self.rl_optimizer = RLDispatchOptimizer()
        self.urgency_classifier = UrgencyClassifier()
        self.rfid_simulator = RFIDSimulator()
        
        self.get_logger().info("WebInterface node initialized")
        self.get_logger().info("  - RFID simulation: enabled")
        self.get_logger().info("  - RL optimization: enabled")
        self.get_logger().info("  - Urgency classification: enabled")
        self.get_logger().info("Dashboard: http://localhost:5000")
    
    def send_task(self, task_number: int) -> Tuple[bool, str]:
        """Send a task to the arm action server."""
        if not _ACTION_AVAILABLE or DexterTask is None:
            return False, "DexterTask action not available"
        
        if not self._lock.acquire(blocking=False):
            return False, "Another task is running"
        
        try:
            if not self.arm_client.wait_for_server(timeout_sec=5.0):
                return False, "Task server not available"
            
            goal = DexterTask.Goal()  # type: ignore[union-attr]
            goal.task_number = task_number
            name = self.TASK_NAMES.get(task_number, str(task_number))
            
            result_holder = {}
            done_event = threading.Event()
            
            def goal_callback(future):
                goal_handle = future.result()
                if not goal_handle or not goal_handle.accepted:
                    result_holder.update({"ok": False, "msg": f"{name} rejected"})
                    done_event.set()
                    return
                goal_handle.get_result_async().add_done_callback(result_callback)
            
            def result_callback(future):
                try:
                    result = future.result()
                    success = result.result.success
                    result_holder.update({
                        "ok": success,
                        "msg": f"{name} {'completed' if success else 'failed'}"
                    })
                except Exception as e:
                    result_holder.update({"ok": False, "msg": str(e)})
                finally:
                    done_event.set()
            
            self.arm_client.send_goal_async(goal).add_done_callback(goal_callback)
            done_event.wait(timeout=30.0)
            
            return result_holder.get("ok", False), result_holder.get("msg", "Timeout")
        
        finally:
            self._lock.release()
    
    def call_dispatch(self, mode: str) -> Tuple[bool, dict]:
        """Call the dispatch service with RL feedback."""
        if not _SRV_AVAILABLE or DispatchItem is None:
            return False, {"msg": "DispatchItem service not available"}
        
        if not self.dispatch_client:
            return False, {"msg": "Inventory node not running"}
        
        if not self.dispatch_client.wait_for_service(timeout_sec=5.0):
            return False, {"msg": "inventory/dispatch service not available"}
        
        # Get pre-dispatch state for RL
        pre_items: List[dict] = []
        pre_state = (0, 0, 0)  # Default state
        if _INV_AVAILABLE:
            try:
                stock = get_stock()
                pre_items = [dict(row) for row in stock]
                pre_state = self.rl_optimizer._get_state(pre_items)
            except Exception as e:
                self.get_logger().warning(f"Failed to get pre-dispatch state: {e}")
        
        req = DispatchItem.Request()  # type: ignore[union-attr]
        req.mode = mode if mode != "RL" else self.rl_optimizer.choose_action(pre_items)
        
        result_holder: Dict[str, Any] = {"ok": False, "msg": "Timeout waiting for service"}
        done_event = threading.Event()
        
        def callback(future):
            try:
                r = future.result()
                result_holder.update({
                    "ok": r.success,
                    "msg": r.message,
                    "item_name": r.item_name,
                    "item_id": r.item_id,
                    "slot": r.slot_number,
                    "expiry": r.expiry_date
                })
            except Exception as e:
                result_holder.update({
                    "ok": False,
                    "msg": f"Service call failed: {str(e)}"
                })
            finally:
                done_event.set()
        
        self.dispatch_client.call_async(req).add_done_callback(callback)
        done_event.wait(timeout=30.0)
        
        # RL feedback
        if result_holder.get("ok") and _INV_AVAILABLE:
            try:
                # Find dispatched item in pre-state
                dispatched_item = next(
                    (i for i in pre_items if i.get("id") == result_holder.get("item_id")), 
                    {}
                )
                if dispatched_item:
                    reward = self.rl_optimizer.calculate_reward(dispatched_item, req.mode)
                    
                    # Get post-dispatch state
                    post_stock = get_stock()
                    post_items = [dict(row) for row in post_stock]
                    post_state = self.rl_optimizer._get_state(post_items)
                    
                    self.rl_optimizer.update(pre_state, req.mode, reward, post_state)
                    result_holder["rl_reward"] = round(reward, 2)
            except Exception as e:
                self.get_logger().warning(f"RL feedback failed: {e}")
        
        return result_holder.get("ok", False), result_holder
    
    def call_add_item(self, item_name: str, slot: int, expiry_ts: str, 
                       rfid_tag: str = "") -> Tuple[bool, str]:
        """Add an item to inventory with RFID tag."""
        if not _SRV_AVAILABLE or AddItemSrv is None:
            return False, "AddItem service not available"
        
        if not self.add_item_client:
            return False, "Inventory node not running"
        
        if not self.add_item_client.wait_for_service(timeout_sec=5.0):
            return False, "inventory/add_item service not available"
        
        # Generate RFID tag if not provided
        if not rfid_tag:
            rfid_tag = self.rfid_simulator.generate_tag()
        
        req = AddItemSrv.Request()  # type: ignore[union-attr]
        req.item_name = item_name
        req.slot = slot
        req.expiry_ts = expiry_ts or ""
        
        result_holder = {}
        done_event = threading.Event()
        
        def callback(future):
            r = future.result()
            result_holder.update({
                "ok": r.success,
                "msg": r.message,
                "item_id": r.item_id if r.success else ""
            })
            done_event.set()
        
        self.add_item_client.call_async(req).add_done_callback(callback)
        done_event.wait(timeout=10.0)
        
        # Register RFID tag
        if result_holder.get("ok"):
            self.rfid_simulator.register_tag(rfid_tag, {
                "item_id": result_holder.get("item_id"),
                "name": item_name,
                "slot": slot,
                "expiry_ts": float(expiry_ts) if expiry_ts else None
            })
            result_holder["rfid_tag"] = rfid_tag
            result_holder["msg"] += f" [RFID: {rfid_tag}]"
        
        return result_holder.get("ok", False), result_holder.get("msg", "Timeout")


# ==============================================================================
# Flask Application
# ==============================================================================

def _find_template_dir() -> str:
    """Locate the templates directory."""
    # Try ament package share directory first
    try:
        from ament_index_python.packages import get_package_share_directory
        share_dir = get_package_share_directory("dexter_remote")
        template_dir = os.path.join(share_dir, "templates")
        if os.path.isdir(template_dir):
            return template_dir
    except Exception:
        pass
    
    # Fallback to relative path from this file
    this_file = Path(__file__).resolve()
    
    # Check parent directories for templates
    for parent in [this_file.parent.parent, this_file.parent]:
        template_dir = parent / "templates"
        if template_dir.is_dir():
            return str(template_dir)
    
    # Last resort: current working directory
    cwd_templates = Path.cwd() / "templates"
    if cwd_templates.is_dir():
        return str(cwd_templates)
    
    return str(this_file.parent.parent / "templates")


app = Flask(__name__, template_folder=_find_template_dir())
ros_node: Optional[WebInterface] = None


# --- Routes ---

@app.route("/")
def index():
    """Serve the main dashboard."""
    return render_template("index.html")


@app.route("/task", methods=["POST"])
def handle_task():
    """Handle arm task requests."""
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not initialized"}), 503
    
    data = flask_request.get_json(silent=True) or {}
    task_num = data.get("task_number")
    
    if task_num is None:
        return jsonify({"success": False, "message": "Missing task_number"}), 400
    
    ok, msg = ros_node.send_task(int(task_num))
    return jsonify({"success": ok, "message": msg}), 200 if ok else 503


@app.route("/inventory/dispatch", methods=["POST"])
def inv_dispatch():
    """Dispatch an item using FIFO, FEFO, or RL-optimized mode."""
    try:
        if ros_node is None:
            return jsonify({"success": False, "message": "ROS node not initialized"}), 503
        
        data = flask_request.get_json(silent=True) or {}
        mode = data.get("mode", "FIFO").upper()
        
        if mode not in ["FIFO", "FEFO", "RL"]:
            return jsonify({"success": False, "message": "Invalid mode"}), 400
        
        ok, result = ros_node.call_dispatch(mode)
        
        if isinstance(result, dict):
            return jsonify({
                "success": ok,
                "message": result.get("msg", ""),
                "item_name": result.get("item_name", ""),
                "slot_number": result.get("slot", -1),
                "expiry": result.get("expiry", ""),
                "rl_reward": result.get("rl_reward")
            }), 200 if ok else 503
        
        return jsonify({"success": False, "message": str(result)}), 503
    
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route("/inventory/add_item", methods=["POST"])
def inv_add_item():
    """Add a new item to inventory."""
    try:
        if ros_node is None:
            return jsonify({"success": False, "message": "ROS node not initialized"}), 503
        
        data = flask_request.get_json(silent=True) or {}
        name = data.get("item_name", "").strip()
        slot = int(data.get("slot", 0))
        expiry = data.get("expiry_ts", "")
        rfid = data.get("rfid_tag", "")
        
        if not name:
            return jsonify({"success": False, "message": "item_name required"}), 400
        
        ok, msg = ros_node.call_add_item(name, slot, expiry, rfid)
        return jsonify({"success": ok, "message": msg}), 200 if ok else 503
    
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route("/inventory/rfid_scan", methods=["POST"])
def inv_rfid_scan():
    """Simulate RFID tag scan."""
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not initialized"}), 503
    
    data = flask_request.get_json(silent=True) or {}
    tag_id = data.get("rfid_tag", "")
    
    if not tag_id:
        # Generate new tag for demo
        tag_id = ros_node.rfid_simulator.generate_tag()
    
    item_data = ros_node.rfid_simulator.scan_tag(tag_id)
    
    return jsonify({
        "success": True,
        "tag_id": tag_id,
        "found": item_data is not None,
        "item": item_data,
        "timestamp": time.time()
    })


@app.route("/inventory/clear", methods=["POST"])
def inv_clear():
    """Clear all inventory data."""
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not initialized"}), 503
    
    if _INV_AVAILABLE:
        clear_all()
        ros_node.rfid_simulator._tags.clear()
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "dexter_inventory not installed"}), 500


@app.route("/inventory/state")
def inv_state():
    """Get current inventory state with urgency and forecast."""
    try:
        if ros_node is None:
            return jsonify({"success": False, "message": "ROS node not initialized"}), 503
        
        if not _INV_AVAILABLE:
            return jsonify({
                "stock_count": 0,
                "low_stock": False,
                "items": [],
                "dispatch_log": [],
                "forecast": None,
                "urgency": {"items": [], "summary": {}, "overall": {"status": "OK"}},
                "rfid_scans": []
            })
        
        stock = get_stock()
        log = get_dispatch_log(10)
        now = time.time()
        
        items_list = []
        for row in stock:
            item_dict = {
                "id": row["id"],
                "name": row["name"],
                "slot": row["slot"],
                "arrival_ts": row["arrival_ts"],
                "expiry_ts": row["expiry_ts"],
                "expiry": format_expiry(row["expiry_ts"])
            }
            items_list.append(item_dict)
        
        # Forecast
        forecast = None
        if ros_node.forecaster:
            try:
                ros_node.forecaster.train()
                forecast = ros_node.forecaster.reorder_recommendation()
            except Exception:
                pass
        
        # Urgency classification
        urgency = ros_node.urgency_classifier.classify_all(items_list)
        
        # RL recommendation
        rl_rec = ros_node.rl_optimizer.get_recommendation(items_list)
        
        # Check low stock
        count = stock_count()
        is_low = count <= 1
        
        return jsonify({
            "timestamp": now,
            "stock_count": count,
            "low_stock": is_low,
            "items": items_list,
            "dispatch_log": [
                {
                    "item_name": r["item_name"],
                    "mode": r["mode"],
                    "slot": r["slot"],
                    "ts": r["ts"]
                }
                for r in log
            ],
            "forecast": forecast,
            "urgency": urgency,
            "rl_recommendation": rl_rec,
            "rfid_scans": ros_node.rfid_simulator.get_scan_history(5)
        })
    
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Error: {str(e)}",
            "stock_count": 0,
            "items": [],
            "dispatch_log": [],
            "urgency": {"items": [], "summary": {}, "overall": {"status": "ERROR"}}
        }), 500


@app.route("/inventory/rl_recommendation")
def inv_rl_recommendation():
    """Get RL-based dispatch recommendation."""
    if ros_node is None:
        return jsonify({"success": False, "message": "ROS node not initialized"}), 503
    
    if not _INV_AVAILABLE:
        return jsonify({"action": "HOLD", "reason": "Inventory not available"})
    
    stock = get_stock()
    items = [dict(row) for row in stock]
    recommendation = ros_node.rl_optimizer.get_recommendation(items)
    
    return jsonify(recommendation)


@app.route("/health")
def health():
    """Health check endpoint."""
    task_server_ready = False
    if ros_node is not None:
        task_server_ready = ros_node.arm_client.server_is_ready()
    
    return jsonify({
        "status": "ok",
        "node_ready": ros_node is not None,
        "task_server_ready": task_server_ready,
        "inventory_ready": _INV_AVAILABLE,
        "services_ready": _SRV_AVAILABLE,
        "features": {
            "rfid_simulation": True,
            "rl_optimization": True,
            "urgency_classification": True,
            "demand_forecasting": _INV_AVAILABLE
        }
    })


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Start the web interface node and Flask server."""
    global ros_node
    
    rclpy.init()
    ros_node = WebInterface()
    
    # Spin ROS in background thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(ros_node,), daemon=True)
    spin_thread.start()
    
    ros_node.get_logger().info("=" * 60)
    ros_node.get_logger().info("  DEXTER FEFO/FIFO Inventory Control System")
    ros_node.get_logger().info("=" * 60)
    ros_node.get_logger().info(f"  Web Dashboard: http://localhost:5000")
    ros_node.get_logger().info(f"  Template dir:  {_find_template_dir()}")
    ros_node.get_logger().info("=" * 60)
    
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
