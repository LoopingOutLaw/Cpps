#!/usr/bin/env python3
"""
train_rl.py — Dexter Inventory Intelligence: Live RL Trainer
=============================================================
Usage:
    python3 train_rl.py                    # train indefinitely
    python3 train_rl.py --episodes 50000   # stop after N episodes
    python3 train_rl.py --port 5001        # custom port (default 5001)
    python3 train_rl.py --load             # resume from saved Q-table
    python3 train_rl.py --fast             # no console animation

Dashboard connects to http://localhost:5001/state (polled every 2s).
Q-table is saved to dexter_qtable.json every 500 episodes.

Environment:
    Perishable goods warehouse — 8 product lines, realistic demand,
    day-of-week seasonality, lead-time uncertainty.

State space (150 states):
    stock_bucket    [0=empty, 1=1unit, 2=2units, 3=3-4, 4=5+]
    expiry_bucket   [0=expired/none, 1=≤1d, 2=2-3d, 3=4-7d, 4=>7d]
    demand_bucket   [0=low, 1=medium, 2=high]
    weekend_flag    [0=weekday, 1=weekend]

Actions:
    0  FIFO    — dispatch oldest item regardless of expiry
    1  FEFO    — dispatch soonest-to-expire item
    2  HOLD    — do not dispatch (wait for better demand)
    3  DISCOUNT— mark-down price to clear expiring stock (-40% revenue)
    4  REORDER — place replenishment order (triggers cost + lead time)

Cost Model:
    unit_cost     = purchase price
    selling_price = normal revenue
    holding_cost  = 0.5% of unit_cost per day per item
    waste_cost    = unit_cost × 1.8   (disposal + lost purchase)
    stockout_cost = selling_price × 1.2  (lost sale + reputational)
    order_cost    = £8 flat fee per order (for EOQ)

Demand Model:
    Gaussian with day-of-week multipliers:
        Mon 0.85  Tue 0.90  Wed 1.00  Thu 1.05
        Fri 1.20  Sat 1.40  Sun 1.10
    Plus normally-distributed noise σ = 30% of mean
    Captures "previous Wednesday's demand ≠ this Wednesday's demand"
"""

import argparse
import json
import math
import os
import random
import sys
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Tuple

# ── ANSI colours ──────────────────────────────────────────────────────────────
R  = '\033[91m'; G  = '\033[92m'; Y  = '\033[93m'
B  = '\033[94m'; M  = '\033[95m'; C  = '\033[96m'
W  = '\033[97m'; DIM = '\033[2m'; RST = '\033[0m'
BOLD = '\033[1m'; CLEAR = '\033[2J\033[H'

# ── PRODUCTS ──────────────────────────────────────────────────────────────────
PRODUCTS = [
    # name, shelf_days, unit_cost, sell_price, base_demand_mean, demand_std
    ("Organic Milk 1L",        7,  1.20, 2.80, 45, 12),
    ("Greek Yogurt 500g",     14,  0.90, 2.20, 30,  8),
    ("Sourdough Bread",        4,  1.50, 3.50, 25,  7),
    ("Baby Spinach 150g",      5,  0.80, 2.00, 20,  6),
    ("Strawberries 400g",      3,  1.80, 4.00, 35, 15),
    ("Free-Range Eggs 12pk",  21,  2.50, 4.50, 40, 10),
    ("Salmon Fillet 200g",     3,  4.50, 9.00, 18,  7),
    ("Mozzarella 125g",       10,  0.70, 1.80, 22,  6),
]

# Day-of-week demand multipliers (0=Mon … 6=Sun)
DOW_MULT = [0.85, 0.90, 1.00, 1.05, 1.20, 1.40, 1.10]

# ── EOQ CALCULATION ───────────────────────────────────────────────────────────
ORDER_FIXED_COST = 8.0  # £ per order

def eoq(annual_demand: float, unit_cost: float, holding_rate: float = 0.005 * 365) -> int:
    """Economic Order Quantity: sqrt(2*D*K / h)."""
    h = unit_cost * holding_rate          # annual holding cost per unit
    q = math.sqrt(2 * annual_demand * ORDER_FIXED_COST / max(h, 0.01))
    return max(1, int(round(q)))

def reorder_point(mean_daily: float, std_daily: float, lead_days: int = 2,
                  service_z: float = 1.645) -> int:
    """ROP = μL + z·σ·√L  (95% service level by default)."""
    return max(1, int(math.ceil(mean_daily * lead_days + service_z * std_daily * math.sqrt(lead_days))))

# ── DEMAND SAMPLER ────────────────────────────────────────────────────────────

class DemandModel:
    """Stochastic demand with day-of-week seasonality + trend noise."""

    def __init__(self, base_mean: float, base_std: float):
        self.base_mean = base_mean
        self.base_std  = base_std
        # Slow-drift trend (mean-reverting)
        self._trend    = 1.0
        self._step     = 0

    def sample(self, dow: int) -> int:
        """Return daily demand integer for a given day-of-week."""
        self._step += 1
        # Slow trend drift (mean-reverts to 1.0 over ~30 days)
        self._trend += random.gauss(0, 0.015)
        self._trend  = 0.7 + 0.3 * self._trend   # gentle clamp
        self._trend  = max(0.5, min(1.8, self._trend))

        mu  = self.base_mean * DOW_MULT[dow] * self._trend
        raw = int(round(max(0, random.gauss(mu, self.base_std * self._trend))))
        return raw

# ── INVENTORY ENVIRONMENT ─────────────────────────────────────────────────────

class InventoryEnv:
    """
    Single-SKU perishable inventory environment.
    Simulates ~1 year of daily decisions per episode.
    """
    DAYS_PER_EPISODE = 365

    def __init__(self, product_idx: int = 0):
        p = PRODUCTS[product_idx]
        self.name       = p[0]
        self.shelf_days = p[1]
        self.unit_cost  = p[2]
        self.sell_price = p[3]
        self.demand     = DemandModel(p[4], p[5])

        self.hold_rate  = 0.005   # 0.5% per day
        self.waste_mult = 1.8
        self.stock_mult = 1.2

        # Compute EOQ and ROP for this product
        annual_d   = p[4] * 365
        self.eoq   = eoq(annual_d, self.unit_cost)
        self.rop   = reorder_point(p[4], p[5])

        self.reset()

    def reset(self) -> Tuple:
        self.day         = 0
        self.dow         = random.randint(0, 6)    # random start day
        self.stock       = []   # list of (age_days, units_remaining)
        self.pending_order: Optional[int] = None   # (units, arrival_day)
        self.lead_day    = 0
        self.total_profit   = 0.0
        self.waste_events   = 0
        self.stockout_events = 0
        # Seed initial stock
        init_units = max(1, int(self.demand.base_mean * 2))
        self.stock.append([0, init_units])
        return self._state()

    # ── State encoding ────────────────────────────────────────────────────────

    def _state(self) -> Tuple[int, int, int, int]:
        total_stock = sum(s[1] for s in self.stock)
        min_age     = min((s[0] for s in self.stock), default=0)
        days_left   = max(0, self.shelf_days - min_age)

        sb = (0 if total_stock == 0 else
              1 if total_stock == 1 else
              2 if total_stock == 2 else
              3 if total_stock <= 4 else 4)

        eb = (0 if days_left == 0 else
              1 if days_left == 1 else
              2 if days_left <= 3 else
              3 if days_left <= 7 else 4)

        d_today = self.demand.sample(self.dow)
        db = (0 if d_today < self.demand.base_mean * 0.7 else
              2 if d_today > self.demand.base_mean * 1.3 else 1)

        wb = 1 if self.dow >= 5 else 0
        return (sb, eb, db, wb)

    # ── Step ──────────────────────────────────────────────────────────────────

    def step(self, action: int) -> Tuple[Tuple, float, bool]:
        reward   = 0.0
        demand   = self.demand.sample(self.dow)
        dispatched = 0

        # Age all batches
        self.stock = [[age + 1, units] for age, units in self.stock]

        # Expire old stock
        fresh, expired_val = [], 0.0
        for age, units in self.stock:
            if age > self.shelf_days:
                expired_val += units * self.unit_cost * self.waste_mult
                self.waste_events += 1
            else:
                fresh.append([age, units])
        self.stock = fresh
        reward -= expired_val

        # Execute action
        if action == 0:   # FIFO — oldest first
            demand, dispatched, rev = self._dispatch_fifo(demand)
            reward += rev
        elif action == 1: # FEFO — soonest-expire first
            demand, dispatched, rev = self._dispatch_fefo(demand)
            reward += rev
        elif action == 2: # HOLD — do nothing
            pass
        elif action == 3: # DISCOUNT — dispatch at 60% price
            demand, dispatched, rev = self._dispatch_fefo(demand, discount=0.60)
            reward += rev
        elif action == 4: # REORDER
            total = sum(s[1] for s in self.stock)
            if total <= self.rop:
                qty = self.eoq
                # Lead time 1-3 days
                lead = random.randint(1, 3)
                self.stock.append([0, qty])  # instant for simplicity; use lead time in advanced version
                reward -= ORDER_FIXED_COST + qty * self.unit_cost * 0.1   # order cost
            else:
                reward -= 2.0   # penalty for unnecessary reorder

        # Stockout penalty for unmet demand after dispatch
        unmet = max(0, demand - dispatched)
        if unmet > 0:
            reward -= unmet * self.sell_price * self.stock_mult
            self.stockout_events += unmet

        # Holding cost for remaining stock
        holding = sum(s[1] for s in self.stock) * self.unit_cost * self.hold_rate
        reward -= holding

        self.total_profit += reward
        self.day += 1
        self.dow  = (self.dow + 1) % 7
        done = self.day >= self.DAYS_PER_EPISODE
        return self._state(), reward, done

    def _dispatch_fifo(self, demand: int, discount: float = 1.0) -> Tuple[int, int, float]:
        dispatched, revenue = 0, 0.0
        sorted_stock = sorted(self.stock, key=lambda x: -x[0])  # oldest first
        for batch in sorted_stock:
            if demand <= 0: break
            sell = min(demand, batch[1])
            batch[1] -= sell
            dispatched += sell
            revenue += sell * self.sell_price * discount
            demand -= sell
        self.stock = [b for b in self.stock if b[1] > 0]
        return demand, dispatched, revenue

    def _dispatch_fefo(self, demand: int, discount: float = 1.0) -> Tuple[int, int, float]:
        dispatched, revenue = 0, 0.0
        sorted_stock = sorted(self.stock, key=lambda x: -x[0])  # highest age (soonest expire)
        for batch in sorted_stock:
            if demand <= 0: break
            sell = min(demand, batch[1])
            batch[1] -= sell
            dispatched += sell
            revenue += sell * self.sell_price * discount
            demand -= sell
        self.stock = [b for b in self.stock if b[1] > 0]
        return demand, dispatched, revenue


# ── Q-LEARNING AGENT ──────────────────────────────────────────────────────────

ACTIONS     = ['FIFO', 'FEFO', 'HOLD', 'DISCOUNT', 'REORDER']
N_ACTIONS   = len(ACTIONS)
ACTION_IDX  = {a: i for i, a in enumerate(ACTIONS)}

class QAgent:
    def __init__(self, alpha: float = 0.15, gamma: float = 0.95,
                 epsilon_start: float = 1.0, epsilon_min: float = 0.05,
                 epsilon_decay: float = 0.9995):
        self.alpha   = alpha
        self.gamma   = gamma
        self.epsilon = epsilon_start
        self.eps_min = epsilon_min
        self.eps_dec = epsilon_decay
        self.q: Dict[Tuple, List[float]] = {}

    def _qv(self, state: Tuple) -> List[float]:
        if state not in self.q:
            self.q[state] = [0.0] * N_ACTIONS
        return self.q[state]

    def act(self, state: Tuple) -> int:
        if random.random() < self.epsilon:
            return random.randrange(N_ACTIONS)
        qv = self._qv(state)
        return qv.index(max(qv))

    def update(self, s: Tuple, a: int, r: float, s2: Tuple, done: bool):
        qv  = self._qv(s)
        q2  = max(self._qv(s2)) if not done else 0.0
        qv[a] += self.alpha * (r + self.gamma * q2 - qv[a])
        if done:
            self.epsilon = max(self.eps_min, self.epsilon * self.eps_dec)

    def best_action(self, state: Tuple) -> str:
        return ACTIONS[self._qv(state).index(max(self._qv(state)))]

    def q_table_export(self) -> dict:
        """Export Q-table in dashboard-compatible format."""
        return {
            str(k): {ACTIONS[i]: round(v, 4) for i, v in enumerate(vs)}
            for k, vs in self.q.items()
        }

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump({'q': {str(k): v for k, v in self.q.items()},
                       'epsilon': self.epsilon}, f)

    def load(self, path: str) -> bool:
        try:
            with open(path) as f:
                data = json.load(f)
            self.q = {eval(k): v for k, v in data['q'].items()}
            self.epsilon = data.get('epsilon', self.eps_min)
            return True
        except Exception:
            return False


# ── SHARED TRAINING STATE (thread-safe) ───────────────────────────────────────

class TrainingState:
    def __init__(self):
        self._lock = threading.Lock()
        self.episode = 0
        self.total_episodes = 0
        self.episode_reward = 0.0
        self.avg_reward_100 = 0.0
        self.best_reward = float('-inf')
        self.epsilon = 1.0
        self.total_waste_events = 0
        self.total_stockout_events = 0
        self.q_table_size = 0
        self.episodes_per_sec = 0.0
        self.reward_history: List[float] = []
        self.q_table_sample: dict = {}
        self.q_table: dict = {}
        self.product_cycling: List[str] = []
        # Cost model metrics
        self.total_profit = 0.0
        self.avg_profit_per_episode = 0.0
        self.waste_rate = 0.0   # % of stock wasted
        self.service_level = 0.0
        self.eoq_data: dict = {}
        self.rop_data: dict = {}
        self.demand_stats: dict = {}
        self.is_training = False
        self.started_at: Optional[float] = None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                'episode':             self.episode,
                'total_episodes':      self.total_episodes,
                'episode_reward':      round(self.episode_reward, 2),
                'avg_reward_100':      round(self.avg_reward_100, 2),
                'best_reward':         round(self.best_reward, 2) if self.best_reward != float('-inf') else 0,
                'epsilon':             round(self.epsilon, 4),
                'total_waste_events':  self.total_waste_events,
                'total_stockout_events': self.total_stockout_events,
                'q_table_size':        self.q_table_size,
                'episodes_per_sec':    round(self.episodes_per_sec, 1),
                'reward_history':      list(self.reward_history[-200:]),
                'q_table_sample':      self.q_table_sample,
                'q_table':             self.q_table,
                'product_cycling':     self.product_cycling,
                'total_profit':        round(self.total_profit, 2),
                'avg_profit_per_episode': round(self.avg_profit_per_episode, 2),
                'waste_rate':          round(self.waste_rate, 4),
                'service_level':       round(self.service_level, 4),
                'eoq_data':            self.eoq_data,
                'rop_data':            self.rop_data,
                'demand_stats':        self.demand_stats,
                'is_training':         self.is_training,
                'uptime_sec':          round(time.time() - self.started_at, 1) if self.started_at else 0,
            }

    def update(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                setattr(self, k, v)


STATE = TrainingState()


# ── HTTP SERVER ───────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass  # suppress access logs

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == '/state':
            body = json.dumps(STATE.snapshot()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/health':
            body = b'{"ok":true}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def run_server(port: int):
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()


# ── CONSOLE DISPLAY ───────────────────────────────────────────────────────────

def bar(val: float, max_val: float, width: int = 20, char: str = '█') -> str:
    filled = int(width * min(1.0, max(0.0, val / max(max_val, 0.001))))
    return char * filled + '░' * (width - filled)

def fmt_reward(r: float) -> str:
    if r > 0:   return f"{G}+{r:8.2f}{RST}"
    if r > -10: return f"{Y}{r:9.2f}{RST}"
    return f"{R}{r:9.2f}{RST}"

def print_dashboard(ep: int, total: int, reward: float, avg: float,
                    best: float, eps: float, waste: int, stockout: int,
                    states: int, speed: float, product: str,
                    profit: float, svc: float, fast: bool):
    if fast: return

    pct = ep / max(total, 1)
    prog_bar = bar(pct, 1.0, 40, '▓')

    print(f"{CLEAR}", end='')
    print(f"{BOLD}{W}╔══════════════════════════════════════════════════════════════╗{RST}")
    print(f"{BOLD}{W}║  {C}DEXTER RL TRAINER{W}  —  Perishable Inventory Optimisation       ║{RST}")
    print(f"{BOLD}{W}╚══════════════════════════════════════════════════════════════╝{RST}")
    print()
    print(f"  {DIM}Training on:{RST}  {Y}{product}{RST}")
    print(f"  {DIM}Progress:   {RST}  [{prog_bar}] {ep:,}/{total:,}  ({pct*100:.1f}%)")
    print(f"  {DIM}Speed:      {RST}  {G}{speed:.0f} ep/s{RST}")
    print()
    print(f"  {'─'*62}")
    print(f"  {BOLD}TRAINING METRICS{RST}")
    print(f"  {'─'*62}")
    print(f"  Episode Reward  : {fmt_reward(reward)}")
    print(f"  Avg (last 100)  : {fmt_reward(avg)}")
    print(f"  Best Reward     : {fmt_reward(best)}")
    print(f"  Avg Profit/Ep   : {fmt_reward(profit)}")
    print(f"  Service Level   : {G if svc > 0.85 else Y if svc > 0.7 else R}{svc*100:.1f}%{RST}")
    print()
    print(f"  {'─'*62}")
    print(f"  {BOLD}EXPLORATION{RST}")
    print(f"  {'─'*62}")
    print(f"  ε (epsilon)     :  {bar(eps, 1.0, 20)} {eps:.4f}")
    print(f"  Q-table states  :  {M}{states:,}{RST}")
    print()
    print(f"  {'─'*62}")
    print(f"  {BOLD}COST EVENTS{RST}")
    print(f"  {'─'*62}")
    print(f"  Waste events    :  {R}{waste:,}{RST}  (items expired unsold)")
    print(f"  Stockout events :  {Y}{stockout:,}{RST}  (demand unmet)")
    print()
    print(f"  {DIM}Dashboard → http://localhost:5001/state{RST}")
    print(f"  {DIM}CTRL+C to stop and save Q-table{RST}")


# ── TRAINING LOOP ─────────────────────────────────────────────────────────────

def compute_eoq_rop_table() -> Tuple[dict, dict]:
    eoq_t, rop_t = {}, {}
    for name, shelf, unit, sell, dmean, dstd in PRODUCTS:
        eoq_t[name] = eoq(dmean * 365, unit)
        rop_t[name] = reorder_point(dmean, dstd)
    return eoq_t, rop_t

def train(total_episodes: int, save_path: str, fast: bool, resume: bool, port: int):
    """Main training loop — runs forever if total_episodes=0."""
    agent = QAgent()
    if resume and os.path.exists(save_path):
        ok = agent.load(save_path)
        print(f"{'Resumed' if ok else 'Fresh start — could not load'}: {save_path}")

    eoq_t, rop_t = compute_eoq_rop_table()

    STATE.update(
        is_training=True,
        started_at=time.time(),
        total_episodes=total_episodes,
        eoq_data=eoq_t,
        rop_data=rop_t,
        demand_stats={
            p[0]: {'mean': p[4], 'std': p[5], 'shelf': p[1],
                   'unit_cost': p[2], 'sell_price': p[3]}
            for p in PRODUCTS
        },
    )

    reward_window = deque(maxlen=100)
    profit_window = deque(maxlen=100)
    total_waste   = 0
    total_stockout = 0
    ep_start_time = time.time()
    speed_window  = deque(maxlen=20)
    last_save     = 0

    ep = 0
    while True:
        if total_episodes > 0 and ep >= total_episodes:
            break

        # Cycle through products (train all of them)
        product_idx = ep % len(PRODUCTS)
        env = InventoryEnv(product_idx)
        state = env.reset()

        ep_reward = 0.0
        done = False
        while not done:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            agent.update(state, action, reward, next_state, done)
            state = next_state
            ep_reward += reward

        ep += 1
        reward_window.append(ep_reward)
        profit_window.append(env.total_profit)
        total_waste    += env.waste_events
        total_stockout += env.stockout_events

        avg100   = sum(reward_window) / len(reward_window)
        best_rew = max(best_rew if ep > 1 else float('-inf'), ep_reward)
        if ep == 1: best_rew = ep_reward

        # Service level: dispatched / total demand (approximated by 1 - stockout rate)
        total_events = total_waste + total_stockout + ep
        svc = max(0.0, 1.0 - total_stockout / max(total_events, 1))

        # Speed
        now = time.time()
        speed_window.append(1.0 / max(now - ep_start_time, 1e-6))
        ep_start_time = now
        speed = sum(speed_window) / len(speed_window)

        # Build Q-table sample (top 12 states by visit count)
        q_sample = {}
        for k, vs in list(agent.q.items())[:12]:
            q_sample[str(k)] = {ACTIONS[i]: round(v, 3) for i, v in enumerate(vs)}

        cycling = [PRODUCTS[i % len(PRODUCTS)][0] for i in range(ep, ep + 4)]

        STATE.update(
            episode=ep,
            episode_reward=ep_reward,
            avg_reward_100=avg100,
            best_reward=best_rew,
            epsilon=agent.epsilon,
            total_waste_events=total_waste,
            total_stockout_events=total_stockout,
            q_table_size=len(agent.q),
            episodes_per_sec=speed,
            reward_history=list(reward_window) + [ep_reward],
            q_table_sample=q_sample,
            q_table=agent.q_table_export() if ep % 100 == 0 else STATE.q_table,
            product_cycling=cycling,
            total_profit=sum(profit_window),
            avg_profit_per_episode=sum(profit_window) / len(profit_window),
            waste_rate=total_waste / max(ep, 1),
            service_level=svc,
        )

        # Console display every 50 episodes
        if ep % 50 == 0:
            print_dashboard(
                ep, total_episodes, ep_reward, avg100, best_rew,
                agent.epsilon, total_waste, total_stockout,
                len(agent.q), speed, PRODUCTS[product_idx][0],
                avg100, svc, fast
            )

        # Save every 500 episodes
        if ep - last_save >= 500:
            agent.save(save_path)
            STATE.update(q_table=agent.q_table_export())
            last_save = ep
            if fast:
                print(f"[ep {ep:,}] avg={avg100:.2f}  ε={agent.epsilon:.4f}  "
                      f"states={len(agent.q)}  waste={total_waste}  svc={svc*100:.1f}%")

    # Final save
    agent.save(save_path)
    STATE.update(q_table=agent.q_table_export(), is_training=False)
    print(f"\n{G}Training complete. Q-table saved → {save_path}{RST}")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Dexter RL Trainer')
    parser.add_argument('--episodes', type=int, default=0,
                        help='Number of episodes (0 = infinite)')
    parser.add_argument('--port', type=int, default=5001,
                        help='HTTP server port (default 5001)')
    parser.add_argument('--save', default='dexter_qtable.json',
                        help='Q-table save file')
    parser.add_argument('--load', action='store_true',
                        help='Resume training from saved Q-table')
    parser.add_argument('--fast', action='store_true',
                        help='No console animation (cleaner for piping)')
    args = parser.parse_args()

    # Start HTTP server
    srv_thread = threading.Thread(
        target=run_server, args=(args.port,), daemon=True)
    srv_thread.start()
    print(f"{G}✓ Trainer HTTP server started on port {args.port}{RST}")
    print(f"{C}  Dashboard: open the Dexter dashboard and click '⚙ RL Trainer' tab{RST}")
    print(f"{DIM}  GET http://localhost:{args.port}/state{RST}")
    print()

    # Pre-compute and print EOQ/ROP table
    eoq_t, rop_t = compute_eoq_rop_table()
    print(f"{BOLD}  EOQ / REORDER POINT TABLE{RST}")
    print(f"  {'─'*65}")
    print(f"  {'Product':<30} {'EOQ':>5} {'ROP':>5} {'Shelf':>6} {'Cost':>6} {'Price':>6}")
    print(f"  {'─'*65}")
    for p in PRODUCTS:
        print(f"  {p[0]:<30} {eoq_t[p[0]]:>5} {rop_t[p[0]]:>5} {p[1]:>5}d {p[2]:>5.2f}  {p[3]:>5.2f}")
    print(f"  {'─'*65}")
    print()
    print(f"  Training on {len(PRODUCTS)} products, cycling every episode.")
    print(f"  {'Total episodes: ' + str(args.episodes) if args.episodes else 'Running indefinitely (CTRL+C to stop)'}")
    print()

    try:
        train(args.episodes, args.save, args.fast, args.load, args.port)
    except KeyboardInterrupt:
        print(f"\n{Y}Stopped by user.{RST}")
        STATE.update(is_training=False)
        time.sleep(1)   # let final /state request complete


if __name__ == '__main__':
    main()
