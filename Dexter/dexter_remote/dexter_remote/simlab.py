#!/usr/bin/env python3
from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class SimConfig:
    initial_inventory: int = 120
    shelf_life_days: int = 8
    base_lead_time_days: int = 2
    delay_probability: float = 0.20
    delay_days: int = 2
    unit_cost: float = 7.0
    unit_price: float = 12.0
    holding_cost_per_unit_day: float = 0.08
    spoilage_cost_per_unit: float = 3.0
    stockout_penalty_per_unit: float = 4.0

    demand_base: float = 20.0
    demand_trend_per_day: float = 0.05
    demand_season_amp: float = 8.0
    demand_noise_std: float = 4.0
    demand_spike_prob: float = 0.15
    demand_spike_extra: float = 12.0


class SimLabEngine:
    ACTIONS: List[int] = [0, 10, 20, 30, 40, 50, 70, 90]

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self.config = SimConfig()
        self.q_table: Dict[Tuple[int, int, int], Dict[int, float]] = {}
        self.alpha = 0.12
        self.gamma = 0.95
        self.epsilon = 0.20
        self.day_reports: List[Dict[str, Any]] = []
        self.training_history: List[Dict[str, Any]] = []
        self.last_train_summary: Dict[str, Any] = {}
        self.reset()

    def reset(self, config_overrides: Optional[Dict[str, Any]] = None) -> None:
        if config_overrides:
            for key, value in config_overrides.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

        self.day = 0
        self.on_hand_batches: List[Dict[str, int]] = [{"qty": int(self.config.initial_inventory), "age": 0}]
        self.pipeline_orders: List[Dict[str, int]] = []

        self.total_demand = 0
        self.total_sold = 0
        self.total_shortage = 0
        self.total_expired = 0
        self.total_ordered = 0

        self.revenue = 0.0
        self.procurement_cost = 0.0
        self.holding_cost = 0.0
        self.stockout_cost = 0.0
        self.spoilage_cost = 0.0

        self.day_reports = []

    def _snapshot_runtime(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "on_hand_batches": copy.deepcopy(self.on_hand_batches),
            "pipeline_orders": copy.deepcopy(self.pipeline_orders),
            "total_demand": self.total_demand,
            "total_sold": self.total_sold,
            "total_shortage": self.total_shortage,
            "total_expired": self.total_expired,
            "total_ordered": self.total_ordered,
            "revenue": self.revenue,
            "procurement_cost": self.procurement_cost,
            "holding_cost": self.holding_cost,
            "stockout_cost": self.stockout_cost,
            "spoilage_cost": self.spoilage_cost,
            "day_reports": copy.deepcopy(self.day_reports),
        }

    def _restore_runtime(self, snapshot: Dict[str, Any]) -> None:
        self.day = snapshot["day"]
        self.on_hand_batches = snapshot["on_hand_batches"]
        self.pipeline_orders = snapshot["pipeline_orders"]
        self.total_demand = snapshot["total_demand"]
        self.total_sold = snapshot["total_sold"]
        self.total_shortage = snapshot["total_shortage"]
        self.total_expired = snapshot["total_expired"]
        self.total_ordered = snapshot["total_ordered"]
        self.revenue = snapshot["revenue"]
        self.procurement_cost = snapshot["procurement_cost"]
        self.holding_cost = snapshot["holding_cost"]
        self.stockout_cost = snapshot["stockout_cost"]
        self.spoilage_cost = snapshot["spoilage_cost"]
        self.day_reports = snapshot["day_reports"]

    def _on_hand_qty(self) -> int:
        return int(sum(batch["qty"] for batch in self.on_hand_batches))

    def _pipeline_qty(self) -> int:
        return int(sum(order["qty"] for order in self.pipeline_orders))

    def _forecast_signal(self) -> int:
        base = (
            self.config.demand_base
            + self.config.demand_trend_per_day * self.day
            + self.config.demand_season_amp * math.sin(2.0 * math.pi * self.day / 7.0)
        )
        return int(max(0, round(base)))

    def _sample_demand(self, day: int) -> int:
        baseline = (
            self.config.demand_base
            + self.config.demand_trend_per_day * day
            + self.config.demand_season_amp * math.sin(2.0 * math.pi * day / 7.0)
        )
        noise = self._rng.gauss(0.0, self.config.demand_noise_std)
        spike = self.config.demand_spike_extra if self._rng.random() < self.config.demand_spike_prob else 0.0
        demand = max(0.0, baseline + noise + spike)
        return int(round(demand))

    def _bucket(self, value: int, bounds: List[int]) -> int:
        for idx, bound in enumerate(bounds):
            if value <= bound:
                return idx
        return len(bounds)

    def _state_key(self) -> Tuple[int, int, int]:
        inv_bucket = self._bucket(self._on_hand_qty(), [20, 50, 100, 170])
        pipe_bucket = self._bucket(self._pipeline_qty(), [0, 20, 60, 120])
        fc_bucket = self._bucket(self._forecast_signal(), [10, 20, 35, 50])
        return inv_bucket, pipe_bucket, fc_bucket

    def _q_values(self, state: Tuple[int, int, int]) -> Dict[int, float]:
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.ACTIONS}
        return self.q_table[state]

    def recommend_order(self) -> int:
        state = self._state_key()
        qvals = self._q_values(state)
        return max(self.ACTIONS, key=lambda a: qvals[a])

    def _choose_action(self, explore: bool) -> int:
        if explore and self._rng.random() < self.epsilon:
            return self._rng.choice(self.ACTIONS)
        return self.recommend_order()

    def _consume_fifo(self, qty: int) -> int:
        remaining = qty
        sold = 0
        for batch in self.on_hand_batches:
            if remaining <= 0:
                break
            take = min(batch["qty"], remaining)
            batch["qty"] -= take
            remaining -= take
            sold += take
        self.on_hand_batches = [b for b in self.on_hand_batches if b["qty"] > 0]
        return sold

    def _age_and_expire(self) -> int:
        expired = 0
        for batch in self.on_hand_batches:
            batch["age"] += 1
        kept = []
        for batch in self.on_hand_batches:
            if batch["age"] >= self.config.shelf_life_days:
                expired += batch["qty"]
            else:
                kept.append(batch)
        self.on_hand_batches = kept
        return expired

    def _receive_orders(self) -> int:
        arrivals = [o for o in self.pipeline_orders if o["arrival_day"] <= self.day]
        self.pipeline_orders = [o for o in self.pipeline_orders if o["arrival_day"] > self.day]
        qty = int(sum(o["qty"] for o in arrivals))
        if qty > 0:
            self.on_hand_batches.append({"qty": qty, "age": 0})
        return qty

    def _place_order(self, qty: int) -> Tuple[int, int]:
        lead = self.config.base_lead_time_days
        if self._rng.random() < self.config.delay_probability:
            lead += self.config.delay_days
        arrival_day = self.day + lead
        if qty > 0:
            self.pipeline_orders.append({"qty": int(qty), "arrival_day": int(arrival_day)})
        return lead, arrival_day

    def step(self, use_rl: bool = True, forced_order: Optional[int] = None) -> Dict[str, Any]:
        state = self._state_key()
        action = int(forced_order) if forced_order is not None else self._choose_action(explore=use_rl)
        action = max(0, action)

        received = self._receive_orders()

        demand = self._sample_demand(self.day)
        on_hand_before = self._on_hand_qty()
        sold = self._consume_fifo(demand)
        shortage = max(0, demand - sold)

        expired = self._age_and_expire()

        lead_time, arrival_day = self._place_order(action)

        end_inventory = self._on_hand_qty()

        revenue = sold * self.config.unit_price
        procurement = action * self.config.unit_cost
        holding = end_inventory * self.config.holding_cost_per_unit_day
        stockout = shortage * self.config.stockout_penalty_per_unit
        spoilage = expired * self.config.spoilage_cost_per_unit
        profit = revenue - procurement - holding - stockout - spoilage

        self.total_demand += demand
        self.total_sold += sold
        self.total_shortage += shortage
        self.total_expired += expired
        self.total_ordered += action

        self.revenue += revenue
        self.procurement_cost += procurement
        self.holding_cost += holding
        self.stockout_cost += stockout
        self.spoilage_cost += spoilage

        next_state = self._state_key()
        if use_rl and forced_order is None:
            q = self._q_values(state)
            next_q = self._q_values(next_state)
            q[action] += self.alpha * (profit + self.gamma * max(next_q.values()) - q[action])

        report = {
            "day": self.day,
            "forecast_signal": self._forecast_signal(),
            "recommended_order": self.recommend_order(),
            "order_qty": action,
            "received_qty": received,
            "lead_time_days": lead_time,
            "arrival_day": arrival_day,
            "demand": demand,
            "sold": sold,
            "shortage": shortage,
            "expired": expired,
            "on_hand_before": on_hand_before,
            "on_hand_after": end_inventory,
            "pipeline_after": self._pipeline_qty(),
            "revenue": round(revenue, 2),
            "procurement_cost": round(procurement, 2),
            "holding_cost": round(holding, 2),
            "stockout_cost": round(stockout, 2),
            "spoilage_cost": round(spoilage, 2),
            "profit": round(profit, 2),
        }
        self.day_reports.append(report)
        self.day += 1
        return report

    def run_days(self, days: int, use_rl: bool = True, forced_order: Optional[int] = None) -> Dict[str, Any]:
        reports = [self.step(use_rl=use_rl, forced_order=forced_order) for _ in range(max(1, int(days)))]
        return {
            "ran_days": len(reports),
            "reports": reports,
            "state": self.state(),
        }

    def forecast(self, horizon_days: int = 7, samples: int = 120) -> Dict[str, Any]:
        horizon = max(1, int(horizon_days))
        sims = max(20, int(samples))
        expected = []
        for offset in range(horizon):
            values = [self._sample_demand(self.day + offset) for _ in range(sims)]
            avg = sum(values) / len(values)
            p90 = sorted(values)[int(0.9 * (len(values) - 1))]
            expected.append({"day_offset": offset + 1, "mean": round(avg, 1), "p90": int(p90)})
        return {
            "horizon_days": horizon,
            "expected_demand": expected,
            "recommended_order_today": self.recommend_order(),
        }

    def train(self, episodes: int = 120, episode_days: int = 35) -> Dict[str, Any]:
        episodes = max(1, int(episodes))
        episode_days = max(5, int(episode_days))
        original_epsilon = self.epsilon
        results: List[float] = []

        snapshot_q = copy.deepcopy(self.q_table)
        snapshot_cfg = copy.deepcopy(self.config)
        snapshot_runtime = self._snapshot_runtime()

        self.epsilon = 0.35
        for idx in range(episodes):
            self.reset()
            episode_profit = 0.0
            for _d in range(episode_days):
                rep = self.step(use_rl=True)
                episode_profit += rep["profit"]
            results.append(episode_profit)
            total_cost = self.procurement_cost + self.holding_cost + self.stockout_cost + self.spoilage_cost
            fill_rate = (self.total_sold / self.total_demand) if self.total_demand > 0 else 1.0
            self.training_history.append({
                "episode": idx + 1,
                "profit": round(episode_profit, 2),
                "expired": int(self.total_expired),
                "shortage": int(self.total_shortage),
                "fill_rate": round(fill_rate, 3),
                "revenue": round(self.revenue, 2),
                "cost": round(total_cost, 2),
            })

        avg_profit = sum(results) / len(results)
        best_profit = max(results)

        self.epsilon = original_epsilon
        # Keep trained Q-table, but restore runtime environment state and config.
        trained_q = copy.deepcopy(self.q_table)
        self.q_table = trained_q if trained_q else snapshot_q
        self.config = snapshot_cfg

        if len(self.training_history) > 1200:
            self.training_history = self.training_history[-1200:]

        self.last_train_summary = {
            "episodes": episodes,
            "episode_days": episode_days,
            "avg_episode_profit": round(avg_profit, 2),
            "best_episode_profit": round(best_profit, 2),
            "q_states": len(self.q_table),
        }

        self._restore_runtime(snapshot_runtime)

        return dict(self.last_train_summary)

    def state(self) -> Dict[str, Any]:
        total_cost = self.procurement_cost + self.holding_cost + self.stockout_cost + self.spoilage_cost
        fill_rate = (self.total_sold / self.total_demand) if self.total_demand > 0 else 1.0
        return {
            "day": self.day,
            "on_hand": self._on_hand_qty(),
            "pipeline": self._pipeline_qty(),
            "recommended_order": self.recommend_order(),
            "totals": {
                "demand": self.total_demand,
                "sold": self.total_sold,
                "shortage": self.total_shortage,
                "expired": self.total_expired,
                "ordered": self.total_ordered,
                "fill_rate": round(fill_rate, 3),
                "revenue": round(self.revenue, 2),
                "total_cost": round(total_cost, 2),
                "profit": round(self.revenue - total_cost, 2),
            },
            "config": asdict(self.config),
            "last_reports": self.day_reports[-25:],
            "forecast": self.forecast(7, 100),
            "training": {
                "summary": self.last_train_summary,
                "history": self.training_history[-240:],
            },
        }
