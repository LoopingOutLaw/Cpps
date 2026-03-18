#!/usr/bin/env python3
"""
ml_forecast.py
Simple demand forecasting model using linear regression on historical dispatch data.
Satisfies the ML/RL component requirement for the CPPS project.

Usage (standalone test):
    python3 ml_forecast.py

As a module:
    from dexter_inventory.ml_forecast import DemandForecaster
    f = DemandForecaster()
    f.train()
    print(f.predict_next_day())
    print(f.reorder_recommendation())
"""

import time
import numpy as np
from typing import Tuple, List, Optional

from dexter_inventory.inventory_db import get_dispatch_log, init_db


class DemandForecaster:
    """
    Linear regression forecaster trained on dispatch log history.

    The model uses day-of-week and recent rolling average as features,
    predicting how many dispatches are expected in the next 24 hours.
    """

    REORDER_LEAD_DAYS = 2        # assume supplier delivers in 2 days
    SAFETY_STOCK_DAYS = 1        # keep 1 extra day of stock as buffer

    def __init__(self):
        self._weights: Optional[np.ndarray] = None
        self._bias:    float = 0.0
        self._trained: bool  = False
        self._last_demand:    float = 0.0
        self._forecast:       float = 0.0
        init_db()

    # ── Training ─────────────────────────────────────────────────────────

    def _build_dataset(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build (X, y) from dispatch log.
        X features per day: [day_of_week_sin, day_of_week_cos, rolling_avg_3d]
        y: dispatch count that day
        """
        log  = get_dispatch_log(200)
        if not log:
            return np.empty((0, 3)), np.empty(0)

        # Bucket by calendar day
        DAY  = 86400.0
        days: dict = {}
        for row in log:
            bucket = int(row["ts"] // DAY)
            days[bucket] = days.get(bucket, 0) + 1

        if len(days) < 3:
            return np.empty((0, 3)), np.empty(0)

        sorted_days = sorted(days.items())
        counts      = np.array([v for _, v in sorted_days], dtype=float)
        timestamps  = np.array([k * DAY for k, _ in sorted_days])

        X_rows, y_rows = [], []
        for i in range(2, len(counts)):
            dow       = time.localtime(timestamps[i]).tm_wday
            dow_sin   = np.sin(2 * np.pi * dow / 7)
            dow_cos   = np.cos(2 * np.pi * dow / 7)
            roll3     = np.mean(counts[i-3:i])
            X_rows.append([dow_sin, dow_cos, roll3])
            y_rows.append(counts[i])

        return np.array(X_rows), np.array(y_rows)

    def train(self) -> bool:
        """Fit the linear regression model.  Returns True if enough data."""
        X, y = self._build_dataset()
        if len(X) < 3:
            # Insufficient history – use rolling average fallback
            log = get_dispatch_log(14)
            if log:
                DAY     = 86400.0
                now     = time.time()
                recent  = [r for r in log if r["ts"] >= now - 7 * DAY]
                self._last_demand = len(recent) / 7.0
                self._forecast    = self._last_demand
            self._trained = False
            return False

        # Closed-form least squares: w = (X^T X)^-1 X^T y
        X_b = np.column_stack([np.ones(len(X)), X])   # add bias column
        try:
            w    = np.linalg.lstsq(X_b, y, rcond=None)[0]
            self._bias    = w[0]
            self._weights = w[1:]
            self._trained = True
            self._last_demand = float(np.mean(y[-7:])) if len(y) >= 7 else float(np.mean(y))
            self._forecast = float(self._predict_raw())
            return True
        except np.linalg.LinAlgError:
            self._trained = False
            return False

    def _predict_raw(self) -> float:
        """Predict demand for the next calendar day (raw float)."""
        if not self._trained or self._weights is None:
            return max(self._last_demand, 0.0)

        now  = time.time()
        dow  = time.localtime(now).tm_wday
        X_b  = np.array([1.0,
                          np.sin(2 * np.pi * dow / 7),
                          np.cos(2 * np.pi * dow / 7),
                          self._last_demand])
        pred = float(X_b @ np.concatenate([[self._bias], self._weights]))
        return max(pred, 0.0)

    # ── Public API ────────────────────────────────────────────────────────

    def predict_next_day(self) -> float:
        """Return predicted dispatch count for the next 24 hours."""
        if not self._trained:
            self.train()
        return round(self._predict_raw(), 2)

    def reorder_recommendation(self) -> dict:
        """
        Return a reorder recommendation dict:
            {
              "reorder":         bool,
              "order_quantity":  int,
              "reason":          str,
              "predicted_demand": float,
            }
        """
        from dexter_inventory.inventory_db import stock_count
        count    = stock_count()
        demand   = self.predict_next_day()
        safety   = self.SAFETY_STOCK_DAYS * demand
        required = (self.REORDER_LEAD_DAYS * demand) + safety
        qty      = max(0, int(np.ceil(required - count)))
        reorder  = (count - demand * self.REORDER_LEAD_DAYS) <= safety

        return {
            "reorder":          reorder,
            "order_quantity":   qty,
            "current_stock":    count,
            "predicted_demand": demand,
            "reason": (
                f"Stock ({count}) will run out in "
                f"~{count/demand:.1f} days at current demand ({demand:.1f}/day). "
                f"Reorder {qty} units to cover {self.REORDER_LEAD_DAYS}-day lead time."
                if demand > 0 else
                "No recent demand – no reorder needed."
            ),
        }

    def summary(self) -> str:
        """One-line summary string for the dashboard."""
        rec = self.reorder_recommendation()
        if rec["reorder"]:
            return (
                f"⚠ Reorder {rec['order_quantity']} unit(s) – "
                f"forecast {rec['predicted_demand']:.1f}/day, "
                f"stock {rec['current_stock']}"
            )
        return (
            f"Stock OK – forecast {rec['predicted_demand']:.1f}/day, "
            f"stock {rec['current_stock']}"
        )


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    f = DemandForecaster()
    trained = f.train()
    print(f"Model trained: {trained}")
    print(f"Forecast (next 24 h): {f.predict_next_day()} dispatches")
    rec = f.reorder_recommendation()
    print(f"Reorder needed: {rec['reorder']}")
    print(f"Reason: {rec['reason']}")
