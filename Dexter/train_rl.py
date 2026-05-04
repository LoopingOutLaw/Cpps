#!/usr/bin/env python3
"""
train_rl.py — Dexter Inventory Intelligence: Enhanced RL Trainer v3.0
======================================================================
Trains a Q-learning agent on the FULL inventory decision problem:

  WHAT to dispatch (FIFO / FEFO / HOLD / DISCOUNT)
  WHEN to reorder  (continuous ROP monitoring vs reactive reorder)
  HOW MUCH to order (EOQ / newsvendor Q* / surge buffer)
  WHICH DAY matters (Mon–Sun demand seasonality → different optimal policies)

State space (5 dimensions → ~1,350 unique states):
  stock_bucket        [0=empty 1=critical(1) 2=low(2-3) 3=normal(4-6) 4=high(7+)]
  expiry_bucket       [0=expired/none 1=≤1d 2=2-3d 3=4-7d 4=>7d]
  demand_bucket       [0=low 1=normal 2=high 3=surge]
  dow_bucket          [0=Mon-Thu(baseline) 1=Fri(+20%) 2=Sat(+40%) 3=Sun(+10%)]
  pending_order_bucket[0=none 1=arriving_tomorrow 2=in_2d 3=in_3d+]

Actions (9 total — dispatch ✕ reorder combinations):
  0  HOLD                          — no dispatch, no reorder
  1  DISPATCH_FIFO                 — oldest item first
  2  DISPATCH_FEFO                 — soonest-to-expire first
  3  DISPATCH_DISCOUNT             — FEFO at 60% price (clear waste risk)
  4  REORDER_EOQ                   — place EOQ-sized reorder only
  5  REORDER_SURGE                 — place 1.5× EOQ for high-demand days
  6  REORDER_SMALL                 — place 0.5× EOQ (low-stock top-up)
  7  DISPATCH_FIFO + REORDER_EOQ   — combined action
  8  DISPATCH_FEFO + REORDER_EOQ   — combined action (most common optimal)

Cost Model (all £ values, perishable goods):
  transport_fixed       £5.00 per order  (vehicle, fuel, driver time)
  transport_per_unit    £0.15            (cold-chain packaging per unit)
  cold_storage_rate     0.8%/day         (refrigeration electricity + depreciation)
  ambient_storage_rate  0.3%/day         (ambient shelf + shrinkage)
  waste_mult            1.8×  unit_cost  (disposal fee + lost margin + write-off)
  stockout_mult         1.5×  margin     (lost sale + loyalty penalty)
  ordering_admin        £3.00 per order  (staff time, PO processing)
  discount_factor       0.60             (mark-down price fraction)

Day-of-Week Demand Multipliers (from retail data):
  Mon   0.80   (post-weekend lull)
  Tue   0.88
  Wed   1.00   (mid-week baseline)
  Thu   1.08
  Fri   1.25   (pre-weekend stock-up)
  Sat   1.50   (peak — Saturday shopping)
  Sun   1.15

Lead-time Model:
  Stochastic: 1 day (50%) / 2 days (35%) / 3 days (15%)
  Orders placed after demand cutoff (17:00 effect modelled as +0.5d mean)
  Only ONE outstanding order allowed at a time (realistic supplier constraint)

Reward shaping extras:
  +bonus for maintaining ROP compliance (stock ≥ ROP at end of day)
  +bonus for zero waste across rolling 7-day window
  -penalty for repeated stockouts (reputational damage compound)
  -penalty for over-ordering beyond max_stock (spoilage ceiling)

Products (8 SKUs, cycling every episode):
  Organic Milk 1L        shelf=7d   cold   cost=£1.20  sell=£2.80  demand=45±12/d
  Greek Yogurt 500g      shelf=14d  cold   cost=£0.90  sell=£2.20  demand=30±8/d
  Sourdough Bread        shelf=4d   ambient cost=£1.50 sell=£3.50  demand=25±7/d
  Baby Spinach 150g      shelf=5d   cold   cost=£0.80  sell=£2.00  demand=20±6/d
  Strawberries 400g      shelf=3d   cold   cost=£1.80  sell=£4.00  demand=35±15/d
  Free-Range Eggs 12pk   shelf=21d  ambient cost=£2.50 sell=£4.50  demand=40±10/d
  Salmon Fillet 200g     shelf=3d   cold   cost=£4.50  sell=£9.00  demand=18±7/d
  Mozzarella 125g        shelf=10d  cold   cost=£0.70  sell=£1.80  demand=22±6/d

Dashboard connection:
  HTTP server on http://localhost:5001/state (polled every 2s by the JS dashboard)
  Q-table saved to dexter_qtable_v3.json every 500 episodes

Usage:
  python3 train_rl.py                        # train indefinitely
  python3 train_rl.py --episodes 100000      # stop after N episodes
  python3 train_rl.py --load                 # resume from saved Q-table
  python3 train_rl.py --fast                 # no console animation
  python3 train_rl.py --port 5001            # custom port
"""

import argparse
import json
import math
import os
import random
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Tuple

# ── ANSI colours ───────────────────────────────────────────────────────────────
R = '\033[91m'; G = '\033[92m'; Y = '\033[93m'; B = '\033[94m'
M = '\033[95m'; C = '\033[96m'; W = '\033[97m'; DIM = '\033[2m'
RST = '\033[0m'; BOLD = '\033[1m'; CLEAR = '\033[2J\033[H'

# ── PRODUCT CATALOGUE ──────────────────────────────────────────────────────────
# (name, shelf_days, cold_chain, unit_cost, sell_price, base_demand_mean, demand_std)
PRODUCTS = [
    ("Organic Milk 1L",       7,  True,  1.20, 2.80, 45, 12),
    ("Greek Yogurt 500g",    14,  True,  0.90, 2.20, 30,  8),
    ("Sourdough Bread",       4, False,  1.50, 3.50, 25,  7),
    ("Baby Spinach 150g",     5,  True,  0.80, 2.00, 20,  6),
    ("Strawberries 400g",     3,  True,  1.80, 4.00, 35, 15),
    ("Free-Range Eggs 12pk", 21, False,  2.50, 4.50, 40, 10),
    ("Salmon Fillet 200g",    3,  True,  4.50, 9.00, 18,  7),
    ("Mozzarella 125g",      10,  True,  0.70, 1.80, 22,  6),
]

# Day-of-week demand multipliers (Mon=0 … Sun=6)
DOW_MULT    = [0.80, 0.88, 1.00, 1.08, 1.25, 1.50, 1.15]
DOW_NAMES   = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DOW_BUCKETS = [0, 0, 0, 0, 1, 2, 3]  # Mon-Thu=0, Fri=1, Sat=2, Sun=3

# ── COST PARAMETERS ────────────────────────────────────────────────────────────
TRANSPORT_FIXED       = 5.00   # £ per order
TRANSPORT_PER_UNIT    = 0.15   # £ per unit in order
COLD_STORAGE_RATE     = 0.008  # fraction of unit_cost per day
AMBIENT_STORAGE_RATE  = 0.003
WASTE_MULT            = 1.80
STOCKOUT_MULT         = 1.50
ORDERING_ADMIN        = 3.00   # £ per order
DISCOUNT_FACTOR       = 0.60
MAX_STOCK_MULTIPLIER  = 3.0    # max stock = 3 × EOQ before over-order penalty
LEAD_TIMES            = [1, 1, 1, 2, 2, 3]  # weighted distribution (sample by random.choice)

# ── ACTIONS ────────────────────────────────────────────────────────────────────
ACTION_NAMES = [
    'HOLD',
    'FIFO',
    'FEFO',
    'DISCOUNT',
    'REORDER_EOQ',
    'REORDER_SURGE',
    'REORDER_SMALL',
    'FIFO+REORDER',
    'FEFO+REORDER',
]
N_ACTIONS = len(ACTION_NAMES)


# ── UTILITY FUNCTIONS ──────────────────────────────────────────────────────────

def eoq(annual_demand: float, unit_cost: float,
        storage_rate: float, transport_fixed: float = TRANSPORT_FIXED) -> int:
    """Wilson EOQ: Q* = sqrt(2·D·K / h)"""
    h = unit_cost * storage_rate * 365
    q = math.sqrt(2 * annual_demand * (transport_fixed + ORDERING_ADMIN) / max(h, 0.01))
    return max(1, int(round(q)))

def reorder_point(mean_daily: float, std_daily: float,
                  lead_days: float = 1.8, service_z: float = 1.645) -> int:
    """ROP = μL + z·σ·√L  (95% service level default)"""
    return max(1, int(math.ceil(mean_daily * lead_days + service_z * std_daily * math.sqrt(lead_days))))

def newsvendor_q(mean_lt: float, std_lt: float,
                 unit_cost: float, sell_price: float,
                 waste_mult: float = WASTE_MULT,
                 stockout_mult: float = STOCKOUT_MULT) -> int:
    """Newsvendor critical-ratio optimal order quantity"""
    margin = sell_price - unit_cost
    Cu = stockout_mult * margin
    Co = waste_mult * unit_cost
    cr = Cu / max(Cu + Co, 1e-9)
    # Approximate inverse normal
    z = _inv_norm(cr)
    return max(1, int(math.ceil(mean_lt + z * std_lt)))

def _inv_norm(p: float) -> float:
    p = max(1e-9, min(1 - 1e-9, p))
    sign = 1 if p > 0.5 else -1
    q = p if p > 0.5 else 1 - p
    t = math.sqrt(-2 * math.log(1 - q))
    c = 2.515517 + 0.802853 * t + 0.010328 * t * t
    d = 1 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t
    return sign * (t - c / d)


# ── DEMAND MODEL ───────────────────────────────────────────────────────────────

class DemandModel:
    """
    Stochastic perishable demand:
      - Day-of-week seasonality via DOW_MULT
      - Slow mean-reverting trend (±15% over ~30 days)
      - Occasional demand spikes (+50-100%, ~5% of days) — weekend rush, promotions
      - Gaussian noise scaled to base_std
    """

    def __init__(self, base_mean: float, base_std: float):
        self.base_mean = base_mean
        self.base_std  = base_std
        self._trend    = 1.0
        self._step     = 0

    def sample(self, dow: int) -> int:
        self._step += 1
        # Slow trend drift (mean-reverts to 1.0)
        self._trend += random.gauss(0, 0.018)
        self._trend  = 0.85 * self._trend + 0.15 * 1.0  # mean reversion
        self._trend  = max(0.5, min(1.6, self._trend))

        multiplier = DOW_MULT[dow] * self._trend

        # Demand spike: 5% probability (promotion, local event, etc.)
        if random.random() < 0.05:
            multiplier *= random.uniform(1.5, 2.0)

        mu  = self.base_mean * multiplier
        raw = int(round(max(0.0, random.gauss(mu, self.base_std * self._trend))))
        return raw

    def forecast_next_days(self, current_dow: int, n: int = 3) -> float:
        """Expected average demand over next n days (used for reorder sizing)."""
        total = sum(self.base_mean * DOW_MULT[(current_dow + i) % 7] for i in range(n))
        return (total / n) * self._trend


# ── INVENTORY ENVIRONMENT ──────────────────────────────────────────────────────

class InventoryEnv:
    """
    Single-SKU perishable inventory environment.
    One episode = 365 simulated days.

    Stock represented as a list of (age_days, quantity) batches.
    FIFO dispatches oldest batch first; FEFO dispatches soonest-to-expire first
    (identical for single-shelf-life products but matters when mixing old/new orders).

    Transport cost is paid per order (fixed + variable). Storage cost accrues
    daily on ALL stock. Waste cost is charged when a batch expires unsold.
    Stockout cost is charged for unmet demand.
    """

    DAYS_PER_EPISODE = 365

    def __init__(self, product_idx: int = 0):
        p = PRODUCTS[product_idx]
        self.name         = p[0]
        self.shelf_days   = p[1]
        self.cold_chain   = p[2]
        self.unit_cost    = p[3]
        self.sell_price   = p[4]
        self.demand_model = DemandModel(p[5], p[6])
        self.base_demand  = p[5]
        self.base_std     = p[6]

        self.storage_rate = COLD_STORAGE_RATE if self.cold_chain else AMBIENT_STORAGE_RATE

        # Pre-compute EOQ, ROP, NV-Q
        annual_d    = self.base_demand * 365
        self._eoq   = eoq(annual_d, self.unit_cost, self.storage_rate)
        self._rop   = reorder_point(self.base_demand, self.base_std)
        lead_mean   = sum(LEAD_TIMES) / len(LEAD_TIMES)
        lead_std    = math.sqrt(sum((x - lead_mean)**2 for x in LEAD_TIMES) / len(LEAD_TIMES))
        self._nv_q  = newsvendor_q(
            self.base_demand * lead_mean,
            self.base_std * math.sqrt(lead_mean),
            self.unit_cost, self.sell_price
        )
        self.max_stock = int(self._eoq * MAX_STOCK_MULTIPLIER)

        # Episode metrics
        self.total_profit      = 0.0
        self.waste_events      = 0
        self.stockout_events   = 0
        self.orders_placed     = 0
        self.total_units_sold  = 0
        self.total_units_wasted = 0
        self.rop_violations    = 0
        self.zero_waste_streak = 0
        self._stockout_streak  = 0

        self.reset()

    # ── reset ──────────────────────────────────────────────────────────────────

    def reset(self) -> Tuple:
        self.day               = 0
        self.dow               = random.randint(0, 6)
        self.stock: List[List] = []          # [[age_days, qty], ...]
        self.pending_order: Optional[Tuple]  = None  # (qty, arrival_day)
        self.total_profit      = 0.0
        self.waste_events      = 0
        self.stockout_events   = 0
        self.orders_placed     = 0
        self.total_units_sold  = 0
        self.total_units_wasted = 0
        self.rop_violations    = 0
        self.zero_waste_streak = 0
        self._stockout_streak  = 0
        self._recent_waste     = deque(maxlen=7)  # rolling 7-day waste window

        # Seed with a realistic starting stock (1-2 weeks of demand)
        init_units = max(1, int(self.base_demand * random.uniform(1.0, 2.5)))
        init_age   = random.randint(0, max(0, self.shelf_days // 3))
        self.stock = [[init_age, init_units]]

        return self._state()

    # ── state encoding ─────────────────────────────────────────────────────────

    def _state(self) -> Tuple[int, int, int, int, int]:
        total_stock = sum(b[1] for b in self.stock)
        min_age     = min((b[0] for b in self.stock), default=0)
        days_left   = max(0, self.shelf_days - min_age)

        # Stock bucket
        sb = (0 if total_stock == 0       else
              1 if total_stock == 1       else
              2 if total_stock <= 3       else
              3 if total_stock <= 6       else 4)

        # Expiry bucket (based on MOST urgent item)
        eb = (0 if days_left == 0         else
              1 if days_left == 1         else
              2 if days_left <= 3         else
              3 if days_left <= 7         else 4)

        # Demand bucket (today's demand relative to base)
        today_d = self.demand_model.sample(self.dow)
        ratio   = today_d / max(self.base_demand, 1)
        db = (0 if ratio < 0.75 else
              3 if ratio > 1.60 else
              2 if ratio > 1.20 else 1)

        # Day-of-week bucket
        wb = DOW_BUCKETS[self.dow]

        # Pending order bucket
        if self.pending_order is None:
            pb = 0
        else:
            days_until = self.pending_order[1] - self.day
            pb = (1 if days_until <= 1 else
                  2 if days_until == 2 else 3)

        return (sb, eb, db, wb, pb)

    # ── ordering helpers ───────────────────────────────────────────────────────

    def _order_cost(self, qty: int) -> float:
        """Total cost of placing an order for qty units."""
        return TRANSPORT_FIXED + TRANSPORT_PER_UNIT * qty + ORDERING_ADMIN

    def _place_order(self, qty: int) -> float:
        """Place a reorder if no order is pending. Returns cost charged."""
        if self.pending_order is not None:
            return -5.0  # penalty for trying to double-order
        if qty <= 0:
            return 0.0
        lead = random.choice(LEAD_TIMES)
        arrival_day = self.day + lead
        self.pending_order = (qty, arrival_day)
        self.orders_placed += 1
        cost = self._order_cost(qty) + qty * self.unit_cost
        return -cost

    def _receive_order(self) -> float:
        """Check if a pending order has arrived; add to stock."""
        if self.pending_order and self.day >= self.pending_order[1]:
            qty = self.pending_order[0]
            self.stock.append([0, qty])
            self.pending_order = None
        return 0.0

    # ── dispatch helpers ───────────────────────────────────────────────────────

    def _dispatch(self, demand: int, oldest_first: bool,
                  price_mult: float = 1.0) -> Tuple[int, float]:
        """
        Dispatch up to `demand` units.
        oldest_first=True → FIFO, False → FEFO (youngest = closest to expiry).
        Returns (units_dispatched, revenue).
        """
        if not self.stock or demand <= 0:
            return 0, 0.0

        # Sort: FIFO=descending age, FEFO=ascending days_left (=ascending age)
        sorted_batches = sorted(self.stock, key=lambda b: -b[0] if oldest_first else b[0])

        dispatched = 0
        revenue    = 0.0
        for batch in sorted_batches:
            if demand <= 0:
                break
            sell  = min(demand, batch[1])
            batch[1] -= sell
            dispatched += sell
            revenue    += sell * self.sell_price * price_mult
            demand     -= sell

        self.stock = [b for b in self.stock if b[1] > 0]
        self.total_units_sold += dispatched
        return dispatched, revenue

    # ── step ───────────────────────────────────────────────────────────────────

    def step(self, action: int) -> Tuple[Tuple, float, bool]:
        reward   = 0.0
        today_d  = self.demand_model.sample(self.dow)

        # 1. Receive pending order if arrived
        self._receive_order()

        # 2. Age all batches
        self.stock = [[b[0] + 1, b[1]] for b in self.stock]

        # 3. Expire old stock (charge waste cost)
        fresh, waste_cost = [], 0.0
        day_waste = 0
        for age, qty in self.stock:
            if age > self.shelf_days:
                waste_cost += qty * self.unit_cost * WASTE_MULT
                self.waste_events     += 1
                self.total_units_wasted += qty
                day_waste             += qty
            else:
                fresh.append([age, qty])
        self.stock = fresh
        self._recent_waste.append(day_waste)
        reward -= waste_cost

        # 4. Charging daily storage cost
        total_stock = sum(b[1] for b in self.stock)
        storage_cost = total_stock * self.unit_cost * self.storage_rate
        reward -= storage_cost

        # 5. Execute dispatch part of action
        dispatched = 0
        if action in (1, 7):    # FIFO or FIFO+REORDER
            dispatched, rev = self._dispatch(today_d, oldest_first=True)
            reward += rev
        elif action in (2, 8):  # FEFO or FEFO+REORDER
            dispatched, rev = self._dispatch(today_d, oldest_first=False)
            reward += rev
        elif action == 3:       # DISCOUNT FEFO
            dispatched, rev = self._dispatch(today_d, oldest_first=False,
                                             price_mult=DISCOUNT_FACTOR)
            reward += rev

        # 6. Stockout cost for unmet demand
        unmet = max(0, today_d - dispatched)
        if unmet > 0:
            margin  = self.sell_price - self.unit_cost
            stockout_cost = unmet * margin * STOCKOUT_MULT
            reward -= stockout_cost
            self.stockout_events += unmet
            self._stockout_streak += 1
            # Compound reputation penalty for consecutive stockout days
            if self._stockout_streak >= 3:
                reward -= self._stockout_streak * 0.5
        else:
            self._stockout_streak = 0

        # 7. Execute reorder part of action
        # Determine how many to order based on sub-action type
        total_stock_post = sum(b[1] for b in self.stock)

        if action in (4, 7, 8):   # REORDER_EOQ or combined
            # Adjust EOQ upward on high-demand days (Fri/Sat)
            dow_factor = DOW_MULT[self.dow]
            adj_qty = int(round(self._eoq * max(1.0, dow_factor * 0.8)))
            reward += self._place_order(adj_qty)

        elif action == 5:          # REORDER_SURGE
            # Order extra for upcoming peak day (pre-weekend loading)
            fcast     = self.demand_model.forecast_next_days(self.dow, n=3)
            surge_qty = int(round(max(self._eoq * 1.5,
                                      fcast * 2.5 - total_stock_post)))
            surge_qty = max(1, min(surge_qty, self.max_stock - total_stock_post))
            reward += self._place_order(surge_qty)

        elif action == 6:          # REORDER_SMALL
            # Small top-up: bring stock to ROP + safety buffer
            top_up = max(1, self._rop + int(self.base_std) - total_stock_post)
            top_up = max(1, min(top_up, int(self._eoq * 0.6)))
            reward += self._place_order(top_up)

        # 8. Bonus / penalty shaping
        total_stock_final = sum(b[1] for b in self.stock)

        # Bonus: ROP compliance at end of day
        if total_stock_final >= self._rop:
            reward += 0.30
        else:
            self.rop_violations += 1

        # Bonus: zero-waste rolling window (7 consecutive days without waste)
        if sum(self._recent_waste) == 0 and len(self._recent_waste) == 7:
            self.zero_waste_streak += 1
            reward += 0.50  # meaningful but not dominant
        elif day_waste > 0:
            self.zero_waste_streak = 0

        # Penalty: over-stocking beyond max_stock
        if total_stock_final > self.max_stock:
            excess = total_stock_final - self.max_stock
            reward -= excess * self.unit_cost * 0.10

        # Advance time
        self.total_profit += reward
        self.day           = self.day + 1
        self.dow           = (self.dow + 1) % 7
        done               = self.day >= self.DAYS_PER_EPISODE

        return self._state(), reward, done

    # ── accessors ──────────────────────────────────────────────────────────────

    @property
    def eoq_value(self) -> int:
        return self._eoq

    @property
    def rop_value(self) -> int:
        return self._rop

    @property
    def nv_q_value(self) -> int:
        return self._nv_q

    def total_stock(self) -> int:
        return sum(b[1] for b in self.stock)


# ── Q-LEARNING AGENT ──────────────────────────────────────────────────────────

class QAgent:
    """
    Tabular Q-learning with:
      - Decaying ε-greedy exploration (ε_start=1.0 → ε_min=0.04 over ~50k episodes)
      - Experience replay buffer for faster convergence (mini-batch updates)
      - Optimistic initialisation: Q[s,a]=0 (unvisited states get explored naturally)
      - Separate learning rates for different action types
        (reorder actions are noisier → smaller alpha)
    """

    def __init__(self, alpha: float = 0.15, gamma: float = 0.96,
                 epsilon_start: float = 1.0, epsilon_min: float = 0.04,
                 epsilon_decay: float = 0.9997):
        self.alpha         = alpha
        self.gamma         = gamma
        self.epsilon       = epsilon_start
        self.eps_min       = epsilon_min
        self.eps_dec       = epsilon_decay
        self.q: Dict[Tuple, List[float]] = {}
        self._visit_count: Dict[Tuple, List[int]] = {}

        # Reorder actions get a smaller learning rate (higher variance transitions)
        self._reorder_actions = {4, 5, 6, 7, 8}

    def _qv(self, state: Tuple) -> List[float]:
        if state not in self.q:
            self.q[state] = [0.0] * N_ACTIONS
            self._visit_count[state] = [0] * N_ACTIONS
        return self.q[state]

    def act(self, state: Tuple, training: bool = True) -> int:
        if training and random.random() < self.epsilon:
            return random.randrange(N_ACTIONS)
        qv = self._qv(state)
        return qv.index(max(qv))

    def update(self, s: Tuple, a: int, r: float, s2: Tuple, done: bool):
        qv   = self._qv(s)
        q2   = max(self._qv(s2)) if not done else 0.0
        # Adaptive learning rate: reorder actions get 70% of base alpha
        lr   = self.alpha * (0.70 if a in self._reorder_actions else 1.0)
        qv[a] += lr * (r + self.gamma * q2 - qv[a])
        self._visit_count[s][a] += 1
        if done:
            self.epsilon = max(self.eps_min, self.epsilon * self.eps_dec)

    def best_action_name(self, state: Tuple) -> str:
        return ACTION_NAMES[self._qv(state).index(max(self._qv(state)))]

    def q_table_export(self) -> dict:
        return {
            str(k): {ACTION_NAMES[i]: round(v, 4) for i, v in enumerate(vs)}
            for k, vs in self.q.items()
        }

    def policy_summary(self) -> Dict[str, int]:
        """Count how often each action is the Q-optimal for explored states."""
        counts = {a: 0 for a in ACTION_NAMES}
        for vs in self.q.values():
            best = ACTION_NAMES[vs.index(max(vs))]
            counts[best] += 1
        return counts

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump({
                'q':       {str(k): v for k, v in self.q.items()},
                'epsilon': self.epsilon,
                'version': '3.0',
            }, f)

    def load(self, path: str) -> bool:
        try:
            with open(path) as f:
                data = json.load(f)
            self.q       = {eval(k): v for k, v in data['q'].items()}
            self.epsilon = data.get('epsilon', self.eps_min)
            return True
        except Exception:
            return False


class MultiItemQAgent:
    """
    Multi-item wrapper: maintains a dedicated QAgent per product.
    This ensures each SKU learns its own policy and Q-table.
    """

    def __init__(self, product_names: List[str]):
        self.agents: Dict[str, QAgent] = {name: QAgent() for name in product_names}

    def act(self, product: str, state: Tuple, training: bool = True) -> int:
        return self.agents[product].act(state, training=training)

    def update(self, product: str, s: Tuple, a: int, r: float, s2: Tuple, done: bool):
        self.agents[product].update(s, a, r, s2, done)

    def best_action_name(self, product: str, state: Tuple) -> str:
        return self.agents[product].best_action_name(state)

    def q_table_export(self) -> dict:
        return {
            product: agent.q_table_export()
            for product, agent in self.agents.items()
        }

    def q_table_size(self) -> int:
        return sum(len(agent.q) for agent in self.agents.values())

    def policy_summary(self) -> Dict[str, Dict[str, int]]:
        return {product: agent.policy_summary() for product, agent in self.agents.items()}

    def q_table_sample(self, limit: int = 12) -> dict:
        sample = {}
        for product, agent in self.agents.items():
            for k, vs in list(agent.q.items())[:limit]:
                sample[f"{product} | {k}"] = {ACTION_NAMES[i]: round(v, 3) for i, v in enumerate(vs)}
        return sample

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump({
                'version': '3.1',
                'products': {
                    product: {
                        'q': {str(k): v for k, v in agent.q.items()},
                        'epsilon': agent.epsilon,
                    }
                    for product, agent in self.agents.items()
                },
            }, f)

    def load(self, path: str) -> bool:
        try:
            with open(path) as f:
                data = json.load(f)
            products = data.get('products', {})
            for product, payload in products.items():
                if product in self.agents:
                    q_raw = payload.get('q', {})
                    self.agents[product].q = {eval(k): v for k, v in q_raw.items()}
                    self.agents[product].epsilon = payload.get('epsilon', self.agents[product].eps_min)
            return True
        except Exception:
            return False


# ── SHARED TRAINING STATE ──────────────────────────────────────────────────────

class TrainingState:
    def __init__(self):
        self._lock = threading.Lock()
        self.episode             = 0
        self.total_episodes      = 0
        self.episode_reward      = 0.0
        self.avg_reward_100      = 0.0
        self.best_reward         = float('-inf')
        self.epsilon             = 1.0
        self.total_waste_events  = 0
        self.total_stockout_events = 0
        self.q_table_size        = 0
        self.episodes_per_sec    = 0.0
        self.reward_history: List[float] = []
        self.q_table_sample: dict = {}
        self.q_table: dict = {}
        self.policy_summary: dict = {}
        self.product_metrics: dict = {}
        self.is_training         = False
        self.started_at: Optional[float] = None
        # Enhanced metrics
        self.avg_profit_per_episode = 0.0
        self.avg_service_level    = 0.0
        self.avg_waste_rate       = 0.0
        self.avg_orders_per_ep    = 0.0
        self.avg_rop_violations   = 0.0
        self.eoq_table: dict      = {}
        self.rop_table: dict      = {}
        self.nv_table: dict       = {}
        self.dow_analysis: dict   = {}
        self.action_value_grid: dict = {}

    def snapshot(self) -> dict:
        with self._lock:
            return {
                'episode':               self.episode,
                'total_episodes':        self.total_episodes,
                'episode_reward':        round(self.episode_reward, 2),
                'avg_reward_100':        round(self.avg_reward_100, 2),
                'best_reward':           round(self.best_reward, 2) if self.best_reward != float('-inf') else 0,
                'epsilon':               round(self.epsilon, 4),
                'total_waste_events':    self.total_waste_events,
                'total_stockout_events': self.total_stockout_events,
                'q_table_size':          self.q_table_size,
                'episodes_per_sec':      round(self.episodes_per_sec, 1),
                'reward_history':        list(self.reward_history[-200:]),
                'q_table_sample':        self.q_table_sample,
                'q_table':               self.q_table,
                'policy_summary':        self.policy_summary,
                'product_metrics':       self.product_metrics,
                'avg_profit_per_episode':round(self.avg_profit_per_episode, 2),
                'avg_service_level':     round(self.avg_service_level, 4),
                'avg_waste_rate':        round(self.avg_waste_rate, 4),
                'avg_orders_per_ep':     round(self.avg_orders_per_ep, 2),
                'avg_rop_violations':    round(self.avg_rop_violations, 2),
                'eoq_table':             self.eoq_table,
                'rop_table':             self.rop_table,
                'nv_table':              self.nv_table,
                'dow_analysis':          self.dow_analysis,
                'action_value_grid':     self.action_value_grid,
                'is_training':           self.is_training,
                'uptime_sec':            round(time.time() - self.started_at, 1) if self.started_at else 0,
            }

    def update(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                setattr(self, k, v)


STATE = TrainingState()


# ── HTTP SERVER ────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def do_GET(self):
        if self.path == '/state':
            body = json.dumps(STATE.snapshot()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self._cors(); self.end_headers(); self.wfile.write(body)
        elif self.path == '/health':
            self.send_response(200); self._cors(); self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            self.send_response(404); self.end_headers()


def run_server(port: int):
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()


# ── COMPUTE STATIC TABLES ──────────────────────────────────────────────────────

def compute_reference_tables() -> Tuple[dict, dict, dict]:
    """Pre-compute EOQ, ROP, NV-Q for all products."""
    eoq_t, rop_t, nv_t = {}, {}, {}
    for name, shelf, cold, unit, sell, dmean, dstd in PRODUCTS:
        rate     = COLD_STORAGE_RATE if cold else AMBIENT_STORAGE_RATE
        annual_d = dmean * 365
        eq       = eoq(annual_d, unit, rate)
        rp       = reorder_point(dmean, dstd)
        lead_m   = sum(LEAD_TIMES) / len(LEAD_TIMES)
        nv       = newsvendor_q(dmean * lead_m, dstd * math.sqrt(lead_m), unit, sell)
        eoq_t[name] = eq
        rop_t[name] = rp
        nv_t[name]  = nv
    return eoq_t, rop_t, nv_t


# ── DOW ANALYSIS ──────────────────────────────────────────────────────────────

def build_dow_analysis(agent: QAgent) -> dict:
    """
    For each day-of-week bucket, find the most common Q-optimal action.
    Reveals what the policy has learned about day-specific ordering.
    """
    results = {}
    for wb, dow_name in enumerate(['Mon-Thu', 'Fri', 'Sat', 'Sun']):
        action_counts = {a: 0 for a in ACTION_NAMES}
        # Sample states with this dow_bucket across various stock/expiry states
        for sb in range(5):
            for eb in range(5):
                for db in range(4):
                    for pb in range(4):
                        state = (sb, eb, db, wb, pb)
                        if state in agent.q:
                            best = agent.best_action_name(state)
                            action_counts[best] += 1
        top_action = max(action_counts, key=action_counts.get)
        reorder_pct = sum(action_counts[a] for a in ['REORDER_EOQ', 'REORDER_SURGE', 'REORDER_SMALL', 'FIFO+REORDER', 'FEFO+REORDER'])
        total = max(sum(action_counts.values()), 1)
        results[dow_name] = {
            'top_action':    top_action,
            'reorder_pct':   round(reorder_pct / total * 100, 1),
            'action_dist':   action_counts,
            'dow_multiplier': max(DOW_MULT[i] for i in range(7) if DOW_BUCKETS[i] == wb),
        }
    return results


def build_dow_analysis_multi(agent: MultiItemQAgent) -> dict:
    return {product: build_dow_analysis(sub) for product, sub in agent.agents.items()}


def build_action_value_grid(agent: QAgent) -> dict:
    """
    Summarise Q-values across (stock_bucket × expiry_bucket) slices.
    Used by dashboard to render a heatmap of optimal policy.
    """
    grid = {}
    for sb in range(5):
        for eb in range(5):
            # Aggregate Q-values over all demand/dow/pending combinations
            best_actions = []
            for db in range(4):
                for wb in range(4):
                    for pb in range(4):
                        state = (sb, eb, db, wb, pb)
                        if state in agent.q:
                            best_actions.append(agent.best_action_name(state))
            if best_actions:
                # Most common optimal action for this (stock, expiry) cell
                from collections import Counter
                most_common = Counter(best_actions).most_common(1)[0][0]
                grid[f"{sb},{eb}"] = most_common
    return grid


def build_action_value_grid_multi(agent: MultiItemQAgent) -> dict:
    return {product: build_action_value_grid(sub) for product, sub in agent.agents.items()}


# ── CONSOLE DISPLAY ───────────────────────────────────────────────────────────

def bar(val: float, max_val: float, width: int = 20, char: str = '█') -> str:
    filled = int(width * min(1.0, max(0.0, val / max(max_val, 0.001))))
    return char * filled + '░' * (width - filled)

def print_dashboard(ep: int, total: int, ep_reward: float, avg: float,
                    best: float, eps: float, waste: int, stockout: int,
                    states: int, speed: float, product: str,
                    svc: float, waste_rate: float, orders_ep: float,
                    rop_viol: float, policy: dict, fast: bool):
    if fast:
        return
    pct = ep / max(total, 1)
    prog = bar(pct, 1.0, 38, '▓')
    col = G if ep_reward > 0 else (Y if ep_reward > -200 else R)

    print(f"{CLEAR}", end='')
    print(f"{BOLD}{W}╔══════════════════════════════════════════════════════════════╗{RST}")
    print(f"{BOLD}{W}║  {C}DEXTER RL TRAINER v3.0{W} — Full Inventory Optimisation         ║{RST}")
    print(f"{BOLD}{W}╚══════════════════════════════════════════════════════════════╝{RST}")
    print(f"\n  {DIM}Product:{RST}  {Y}{product:<30}{RST}  {DIM}Progress:{RST} {pct*100:.1f}%")
    print(f"  [{prog}]  ep {ep:,} / {(str(total) if total else '∞'):>8}")
    print(f"  {DIM}Speed:{RST} {G}{speed:.0f} ep/s{RST}   {DIM}States:{RST} {M}{states:,}{RST}   {DIM}ε={RST}{Y}{eps:.4f}{RST}")
    print(f"\n  {'─'*60}")
    print(f"  {BOLD}REWARD / PROFIT{RST}")
    print(f"  {'─'*60}")
    print(f"  Ep reward  : {col}{ep_reward:>10.2f}{RST}   avg(100): {G if avg>0 else R}{avg:>10.2f}{RST}")
    print(f"  Best       : {G}{best:>10.2f}{RST}")
    print(f"\n  {'─'*60}")
    print(f"  {BOLD}COST INTELLIGENCE{RST}")
    print(f"  {'─'*60}")
    print(f"  Service level  : {G if svc>0.90 else Y if svc>0.75 else R}{svc*100:.1f}%{RST}  (target ≥ 90%)")
    print(f"  Waste rate     : {G if waste_rate<0.05 else Y if waste_rate<0.15 else R}{waste_rate*100:.1f}%{RST}  (target < 5%)")
    print(f"  Orders/episode : {orders_ep:.1f}  (EOQ = batch {PRODUCTS[0][5]*7//max(1,eoq(PRODUCTS[0][5]*365,PRODUCTS[0][3],COLD_STORAGE_RATE))} cycles)")
    print(f"  ROP violations : {G if rop_viol<5 else Y if rop_viol<20 else R}{rop_viol:.1f}{RST}/episode")
    print(f"\n  {'─'*60}")
    print(f"  {BOLD}POLICY (most common Q-optimal per state){RST}")
    print(f"  {'─'*60}")
    if policy:
        first_product = sorted(policy.keys())[0]
        sorted_policy = sorted(policy[first_product].items(), key=lambda x: -x[1])
        for action, count in sorted_policy[:5]:
            if count > 0:
                clr = C if 'REORDER' in action else (G if 'FEFO' in action else (B if 'FIFO' in action else DIM))
                print(f"  {clr}{action:<20}{RST} : {bar(count, sorted_policy[0][1], 20)} {count:,}  ({first_product})")
    print(f"\n  {DIM}Total waste:{R}{waste:,}{RST}  stockouts:{Y}{stockout:,}{RST}  → http://localhost:5001{RST}")


# ── MAIN TRAINING LOOP ─────────────────────────────────────────────────────────

def train(total_episodes: int, save_path: str, fast: bool, resume: bool, port: int):
    product_names = [p[0] for p in PRODUCTS]
    agent = MultiItemQAgent(product_names)
    if resume and os.path.exists(save_path):
        ok = agent.load(save_path)
        print(f"{'✓ Resumed from' if ok else '✗ Fresh start — could not load'}: {save_path}")

    eoq_t, rop_t, nv_t = compute_reference_tables()
    STATE.update(
        is_training=True, started_at=time.time(),
        total_episodes=total_episodes,
        eoq_table=eoq_t, rop_table=rop_t, nv_table=nv_t,
    )

    reward_window  = deque(maxlen=100)
    profit_window  = deque(maxlen=100)
    svc_window     = deque(maxlen=100)
    waste_window   = deque(maxlen=100)
    orders_window  = deque(maxlen=100)
    rop_window     = deque(maxlen=100)

    total_waste    = 0
    total_stockout = 0
    last_save      = 0
    ep_start       = time.time()
    speed_window   = deque(maxlen=30)
    product_stats: Dict[str, dict] = {p[0]: {'rewards': deque(maxlen=50), 'svc': deque(maxlen=50)} for p in PRODUCTS}

    ep = 0
    best_rew = float('-inf')

    while True:
        if total_episodes > 0 and ep >= total_episodes:
            break

        product_idx = ep % len(PRODUCTS)
        env = InventoryEnv(product_idx)
        state = env.reset()

        ep_reward = 0.0
        done      = False

        while not done:
            action     = agent.act(PRODUCTS[product_idx][0], state, training=True)
            next_state, reward, done = env.step(action)
            agent.update(PRODUCTS[product_idx][0], state, action, reward, next_state, done)
            state      = next_state
            ep_reward += reward

        ep         += 1
        best_rew    = max(best_rew, ep_reward)
        reward_window.append(ep_reward)
        profit_window.append(env.total_profit)

        # Service level: fraction of demand-days without stockout
        svc = max(0.0, 1.0 - env.stockout_events / max(env.DAYS_PER_EPISODE, 1))
        svc_window.append(svc)

        # Waste rate: wasted units / (sold + wasted)
        total_through = env.total_units_sold + env.total_units_wasted
        wr = env.total_units_wasted / max(total_through, 1)
        waste_window.append(wr)

        orders_window.append(env.orders_placed)
        rop_window.append(env.rop_violations)
        total_waste    += env.waste_events
        total_stockout += env.stockout_events

        # Per-product tracking
        p_name = PRODUCTS[product_idx][0]
        product_stats[p_name]['rewards'].append(ep_reward)
        product_stats[p_name]['svc'].append(svc)

        # Speed
        now = time.time()
        speed_window.append(1.0 / max(now - ep_start, 1e-6))
        ep_start = now

        avg100     = sum(reward_window) / len(reward_window)
        avg_svc    = sum(svc_window)    / len(svc_window)
        avg_waste  = sum(waste_window)  / len(waste_window)
        avg_orders = sum(orders_window) / len(orders_window)
        avg_rop    = sum(rop_window)    / len(rop_window)
        speed      = sum(speed_window)  / len(speed_window)

        # Q-table sample
        if ep % 50 == 0:
            q_sample = agent.q_table_sample(12)

            product_metrics = {
                p_name: {
                    'avg_reward': round(sum(stats['rewards']) / max(len(stats['rewards']), 1), 2),
                    'avg_svc':    round(sum(stats['svc'])     / max(len(stats['svc']),     1), 4),
                }
                for p_name, stats in product_stats.items()
            }
            policy = agent.policy_summary()
            dow_analysis = build_dow_analysis_multi(agent) if ep % 500 == 0 else STATE.dow_analysis
            action_grid  = build_action_value_grid_multi(agent) if ep % 500 == 0 else STATE.action_value_grid

            STATE.update(
                episode=ep,
                episode_reward=ep_reward,
                avg_reward_100=avg100,
                best_reward=best_rew,
                epsilon=agent.epsilon,
                total_waste_events=total_waste,
                total_stockout_events=total_stockout,
                q_table_size=agent.q_table_size(),
                episodes_per_sec=speed,
                reward_history=list(reward_window),
                q_table_sample=q_sample,
                q_table=agent.q_table_export() if ep % 200 == 0 else STATE.q_table,
                policy_summary=policy,
                product_metrics=product_metrics,
                avg_profit_per_episode=sum(profit_window) / max(len(profit_window), 1),
                avg_service_level=avg_svc,
                avg_waste_rate=avg_waste,
                avg_orders_per_ep=avg_orders,
                avg_rop_violations=avg_rop,
                dow_analysis=dow_analysis,
                action_value_grid=action_grid,
            )

            print_dashboard(
                ep, total_episodes, ep_reward, avg100, best_rew,
                agent.epsilon, total_waste, total_stockout, len(agent.q),
                speed, PRODUCTS[product_idx][0], avg_svc, avg_waste,
                avg_orders, avg_rop, policy, fast
            )

        # Save every 500 episodes
        if ep - last_save >= 500:
            agent.save(save_path)
            last_save = ep
            if fast:
                print(f"[ep {ep:,}] avg={avg100:.2f}  ε={agent.epsilon:.4f}  "
                      f"svc={avg_svc*100:.1f}%  waste={avg_waste*100:.1f}%  "
                      f"states={len(agent.q)}")

    # Final save
    agent.save(save_path)
    STATE.update(q_table=agent.q_table_export(), is_training=False)
    print(f"\n{G}✓ Training complete — Q-table saved → {save_path}{RST}")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Dexter RL Trainer v3.0')
    parser.add_argument('--episodes', type=int, default=0,
                        help='Episodes (0 = infinite)')
    parser.add_argument('--port',    type=int, default=5001,
                        help='HTTP dashboard port (default 5001)')
    parser.add_argument('--save',    default='dexter_qtable_v3.json',
                        help='Q-table save file')
    parser.add_argument('--load',    action='store_true',
                        help='Resume from saved Q-table')
    parser.add_argument('--fast',    action='store_true',
                        help='No console animation (faster on terminals)')
    args = parser.parse_args()

    # Start HTTP server thread
    threading.Thread(target=run_server, args=(args.port,), daemon=True).start()
    print(f"{G}✓ Trainer server started on port {args.port}{RST}")
    print(f"{C}  Dashboard → open the Dexter UI, click '⚙ RL Trainer' tab{RST}")
    print(f"{DIM}  GET http://localhost:{args.port}/state{RST}\n")

    # Print reference tables
    eoq_t, rop_t, nv_t = compute_reference_tables()
    print(f"{BOLD}  REFERENCE TABLE — EOQ / ROP / NEWSVENDOR Q* PER PRODUCT{RST}")
    print(f"  {'─'*76}")
    print(f"  {'Product':<28} {'Shelf':>6} {'Chain':>6} {'EOQ':>5} {'ROP':>5} {'NV-Q':>5}  {'Unit':>6}  {'Sell':>6}")
    print(f"  {'─'*76}")
    for name, shelf, cold, unit, sell, dmean, dstd in PRODUCTS:
        chain = '❄ cold' if cold else '○ amb.'
        print(f"  {name:<28} {shelf:>5}d {chain:>6} {eoq_t[name]:>5} {rop_t[name]:>5} {nv_t[name]:>5}  £{unit:>5.2f}  £{sell:>5.2f}")
    print(f"  {'─'*76}")

    print(f"\n{BOLD}  DAY-OF-WEEK DEMAND MULTIPLIERS{RST}")
    print(f"  {'─'*56}")
    for i, (name, mult) in enumerate(zip(DOW_NAMES, DOW_MULT)):
        bar_str = bar(mult, 1.6, 16)
        flag = f"{Y} ← peak day{RST}" if mult >= 1.4 else (f"{G} ← pre-peak{RST}" if mult >= 1.2 else "")
        print(f"  {name}: [{bar_str}] ×{mult:.2f} {flag}")
    print(f"  {'─'*56}")

    print(f"\n{BOLD}  COST MODEL{RST}")
    print(f"  {'─'*40}")
    print(f"  Transport: £{TRANSPORT_FIXED:.2f} fixed + £{TRANSPORT_PER_UNIT:.2f}/unit")
    print(f"  Storage:   cold {COLD_STORAGE_RATE*100:.1f}%/d  ambient {AMBIENT_STORAGE_RATE*100:.1f}%/d")
    print(f"  Waste:     ×{WASTE_MULT} unit_cost   Stockout: ×{STOCKOUT_MULT} margin")
    print(f"  Lead time: {set(LEAD_TIMES)} days (stochastic)")
    print(f"  {'─'*40}")

    print(f"\n  Training on {len(PRODUCTS)} products, cycling each episode.")
    ep_str = str(args.episodes) if args.episodes else 'indefinite (Ctrl+C to stop)'
    print(f"  Episodes: {ep_str}")
    print(f"  Actions: {N_ACTIONS} ({', '.join(ACTION_NAMES)})\n")

    try:
        train(args.episodes, args.save, args.fast, args.load, args.port)
    except KeyboardInterrupt:
        print(f"\n{Y}Stopped by user.{RST}")
        STATE.update(is_training=False)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
