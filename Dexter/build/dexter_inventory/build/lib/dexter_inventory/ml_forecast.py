#!/usr/bin/env python3
"""
ml_forecast.py  –  Dexter Inventory Intelligence: Demand Forecaster
====================================================================
Replaces the old linear-regression-only version.

New model stack:
    1. Holt-Winters double exponential smoothing  (trend)
    2. Day-of-week seasonal indices               (seasonality)
    3. Ensemble via inverse-MAE weighting         (robustness)

Also computes:
    - 7-day probabilistic forecast (point + 80/95% CI)
    - Economic Order Quantity  (EOQ)
    - Reorder Point            (ROP = μ·L + z·σ·√L)
    - Newsvendor optimal order (critical-ratio model)
    - Full cost curve          (waste, stockout, holding, ordering)
    - Day-of-week demand profile

Perishable cost defaults (override via CostParams):
    unit_cost            £2.50 (blended average across 4 ROS slots)
    selling_price        £5.00
    holding_cost_rate    0.5%  per day   (cold chain + storage)
    waste_cost_mult      1.8×  unit_cost (disposal + lost margin)
    stockout_cost_mult   1.2×  margin    (lost sale + reputation)
    ordering_fixed_cost  £8.00 per order
    lead_time_days       2
    service_level        0.92  (92% in-stock target)
"""

import math
import sqlite3
import time
from typing import Dict, List, Optional, Tuple

from dexter_inventory.inventory_db import DB_PATH, init_db


# ── Cost defaults (perishable goods) ─────────────────────────────────────────

DEFAULT_COST = dict(
    unit_cost            = 2.50,
    selling_price        = 5.00,
    holding_cost_rate    = 0.005,   # per day
    waste_cost_mult      = 1.80,
    stockout_cost_mult   = 1.20,
    ordering_fixed_cost  = 8.00,
    lead_time_days       = 2,
    service_level        = 0.92,
)

# Day-of-week labels (0=Monday … 6=Sunday, Python weekday())
DOW_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


# ── Holt-Winters (additive, no seasonality component — handled separately) ───

def holt_winters(series: List[float], alpha: float = 0.30,
                 beta: float = 0.10) -> Tuple[List[float], float, float]:
    """
    Double exponential smoothing.
    Returns (fitted_values, level, trend).
    """
    if len(series) < 2:
        L = series[0] if series else 0.0
        return [L], L, 0.0

    L = series[0]
    T = series[1] - series[0]
    fitted = [L]
    for obs in series[1:]:
        L_new = alpha * obs + (1 - alpha) * (L + T)
        T_new = beta  * (L_new - L) + (1 - beta) * T
        fitted.append(L + T)
        L, T = L_new, T_new
    return fitted, L, T


def hw_predict(level: float, trend: float, h: int = 1) -> float:
    return max(0.0, level + h * trend)


# ── Day-of-week seasonal indices ─────────────────────────────────────────────

def fit_dow_indices(series: List[float], dows: List[int]) -> List[float]:
    """
    Fit multiplicative day-of-week indices (7 values, normalised to mean=1).
    Falls back to flat [1.0]*7 if insufficient data.
    """
    if len(series) < 7:
        return [1.0] * 7

    mu = sum(series) / len(series) or 1.0
    totals = [0.0] * 7
    counts = [0]   * 7
    for v, d in zip(series, dows):
        totals[d] += v
        counts[d] += 1

    raw = [(totals[i] / counts[i] / mu) if counts[i] > 0 else 1.0 for i in range(7)]
    avg = sum(raw) / 7
    return [v / avg for v in raw]          # normalise so mean = 1.0


def dow_predict(mean: float, indices: List[float], h: int = 1) -> float:
    """Predict demand h days ahead using day-of-week index."""
    today_py  = time.localtime().tm_wday   # 0=Mon
    target_dow = (today_py + h - 1) % 7
    return max(0.0, mean * indices[target_dow])


# ── Inverse normal CDF (Abramowitz & Stegun approximation) ───────────────────

def inv_norm(p: float) -> float:
    p = max(1e-9, min(1 - 1e-9, p))
    sign = 1 if p > 0.5 else -1
    q    = p if p > 0.5 else 1 - p
    t    = math.sqrt(-2 * math.log(1 - q))
    c    = 2.515517 + 0.802853 * t + 0.010328 * t ** 2
    d    = 1 + 1.432788 * t + 0.189269 * t ** 2 + 0.001308 * t ** 3
    return sign * (t - c / d)


# ── Data loader ───────────────────────────────────────────────────────────────

def _load_dispatch_series() -> Tuple[List[float], List[int]]:
    """
    Load dispatch log and bucket into daily counts.
    Returns (series, dows) aligned by calendar day.
    """
    init_db()
    DAY = 86400.0
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT ts FROM dispatch_log ORDER BY ts ASC"
            ).fetchall()
    except Exception:
        return [], []

    if not rows:
        return [], []

    buckets: Dict[int, int] = {}
    for (ts,) in rows:
        b = int(ts // DAY)
        buckets[b] = buckets.get(b, 0) + 1

    keys = sorted(buckets)
    series, dows = [], []
    for b in range(keys[0], keys[-1] + 1):
        series.append(float(buckets.get(b, 0)))
        # Python weekday: Mon=0 … Sun=6
        dows.append(int((b * DAY / 86400 + 3) % 7))  # epoch 0 = Thu → offset 3

    return series, dows


# ── Main forecaster class ─────────────────────────────────────────────────────

class DemandForecaster:
    """
    Ensemble (Holt-Winters + DoW seasonal) demand forecaster
    with integrated cost model for perishable goods.
    """

    def __init__(self, cost_params: Optional[dict] = None):
        self.cp      = {**DEFAULT_COST, **(cost_params or {})}
        self._trained = False

        # Model state
        self.series:  List[float] = []
        self.dows:    List[int]   = []
        self.mean:    float = 0.0
        self.std:     float = 0.3
        self.cv:      float = 0.0
        self.hw_level: float = 0.0
        self.hw_trend: float = 0.0
        self.hw_fitted: List[float] = []
        self.dow_idx: List[float] = [1.0] * 7
        self.weights: Tuple[float, float] = (0.5, 0.5)

    # ── Training ──────────────────────────────────────────────────────────────

    def train(self) -> bool:
        """Load dispatch history and fit the ensemble model."""
        series, dows = _load_dispatch_series()
        self.series = series
        self.dows   = dows

        if len(series) < 2:
            # Not enough history — use a sensible prior
            recent = series[-14:] if series else []
            self.mean = sum(recent) / len(recent) if recent else 0.5
            self.std  = max(self.mean * 0.35, 0.05)
            self.cv   = self.std / max(self.mean, 1e-6)
            self._trained = False
            return False

        self.mean = sum(series) / len(series)
        var       = sum((v - self.mean) ** 2 for v in series) / len(series)
        self.std  = max(math.sqrt(var), 0.01)
        self.cv   = self.std / max(self.mean, 1e-6)

        # Fit component models
        self.hw_fitted, self.hw_level, self.hw_trend = holt_winters(series)
        self.dow_idx  = fit_dow_indices(series, dows)

        dow_fitted = [self.mean * self.dow_idx[d] for d in dows]

        # Inverse-MAE ensemble weighting on last 14 days
        n = min(14, len(series))
        hw_mae  = sum(abs(series[i] - self.hw_fitted[i])  for i in range(-n, 0)) / n + 1e-6
        dow_mae = sum(abs(series[i] - dow_fitted[i])       for i in range(-n, 0)) / n + 1e-6
        total   = 1 / hw_mae + 1 / dow_mae
        self.weights = (1 / hw_mae / total, 1 / dow_mae / total)

        self._trained = len(series) >= 7
        return self._trained

    # ── Point forecast ────────────────────────────────────────────────────────

    def predict_next_day(self) -> float:
        hw  = hw_predict(self.hw_level, self.hw_trend, 1)
        dow = dow_predict(self.mean, self.dow_idx, 1)
        return max(0.0, self.weights[0] * hw + self.weights[1] * dow)

    def predict_horizon(self, days: int = 7) -> List[dict]:
        """7-day probabilistic forecast with 80% and 95% confidence intervals."""
        now_ts = time.time()
        results = []
        for h in range(1, days + 1):
            hw  = hw_predict(self.hw_level, self.hw_trend, h)
            dow = dow_predict(self.mean, self.dow_idx, h)
            mu  = max(0.0, self.weights[0] * hw + self.weights[1] * dow)
            # Uncertainty grows with horizon
            sigma = max(self.std * (1 + 0.08 * (h - 1)), 0.05)
            day_ts = now_ts + h * 86400
            dow_name = DOW_NAMES[int((time.localtime(day_ts).tm_wday))]
            import datetime
            dt = datetime.date.fromtimestamp(day_ts)
            results.append(dict(
                day      = h,
                date     = f"{dow_name} {dt.day} {dt.strftime('%b')}",
                forecast = round(mu, 2),
                lo80     = round(max(0.0, mu - 1.282 * sigma), 2),
                hi80     = round(mu + 1.282 * sigma, 2),
                lo95     = round(max(0.0, mu - 1.960 * sigma), 2),
                hi95     = round(mu + 1.960 * sigma, 2),
            ))
        return results

    # ── Day-of-week profile ───────────────────────────────────────────────────

    def dow_profile(self) -> List[dict]:
        return [
            dict(day=DOW_NAMES[i],
                 index=round(self.dow_idx[i], 3),
                 demand=round(self.mean * self.dow_idx[i], 2))
            for i in range(7)
        ]

    # ── Cost model ────────────────────────────────────────────────────────────

    def eoq(self) -> dict:
        """Economic Order Quantity: Q* = sqrt(2·D·K / h)"""
        D   = max(self.predict_next_day() * 365, 0.1)
        K   = self.cp['ordering_fixed_cost']
        h   = self.cp['holding_cost_rate'] * 365 * self.cp['unit_cost']
        q   = max(1, math.ceil(math.sqrt(2 * D * K / max(h, 0.001))))
        return dict(
            eoq               = q,
            annual_demand     = round(D, 1),
            order_cost_pa     = round(K * D / max(q, 1), 2),
            holding_cost_pa   = round(h * q / 2, 2),
        )

    def rop(self) -> dict:
        """Reorder Point: μ·L + z·σ·√L"""
        lt  = self.cp['lead_time_days']
        d   = self.predict_next_day()
        z   = inv_norm(self.cp['service_level'])
        mu  = d * lt
        sig = max(self.std * math.sqrt(max(lt, 1)), 0.05)
        ss  = math.ceil(z * sig)
        return dict(
            rop          = math.ceil(mu + ss),
            safety_stock = ss,
            mu_lt        = round(mu, 2),
            sigma_lt     = round(sig, 2),
            service_z    = round(z, 3),
        )

    def newsvendor(self) -> dict:
        """Newsvendor critical-ratio model optimal order quantity."""
        lt     = self.cp['lead_time_days']
        d      = self.predict_next_day()
        mu_lt  = d * lt
        sig_lt = max(self.std * math.sqrt(max(lt, 1)), 0.1)
        margin = self.cp['selling_price'] - self.cp['unit_cost']
        Cu     = self.cp['stockout_cost_mult']  * margin
        Co     = (self.cp['holding_cost_rate'] * lt
                  + (1 - self.cp['service_level']) * self.cp['waste_cost_mult']
                  * self.cp['unit_cost'])
        cr     = Cu / max(Cu + Co, 1e-9)
        z      = inv_norm(cr)
        q_star = max(0, math.ceil(mu_lt + z * sig_lt))
        return dict(
            optimal_qty    = q_star,
            critical_ratio = round(cr, 4),
            z_score        = round(z, 3),
            mu_lt          = round(mu_lt, 2),
            sigma_lt       = round(sig_lt, 2),
            Cu             = round(Cu, 2),
            Co             = round(Co, 4),
        )

    def cost_curve(self, max_q: Optional[int] = None) -> List[dict]:
        """Full cost breakdown for order quantities 0 … max_q."""
        d     = self.predict_next_day()
        total_d = max(d * 30, 0.01)
        if max_q is None:
            max_q = max(math.ceil(total_d * 2.5) + 1, 10)
        results = []
        for q in range(0, max_q + 1):
            sold     = min(q, total_d)
            wasted   = max(0.0, q - total_d)
            short    = max(0.0, total_d - q)
            margin   = self.cp['selling_price'] - self.cp['unit_cost']
            purchase = q       * self.cp['unit_cost']
            holding  = q       * self.cp['holding_cost_rate'] * 15
            waste    = wasted  * self.cp['waste_cost_mult']   * self.cp['unit_cost']
            stockout = short   * self.cp['stockout_cost_mult'] * margin
            ordering = self.cp['ordering_fixed_cost']
            revenue  = sold    * self.cp['selling_price']
            results.append(dict(
                qty      = q,
                revenue  = round(revenue,  2),
                purchase = round(purchase, 2),
                holding  = round(holding,  2),
                waste    = round(waste,    2),
                stockout = round(stockout, 2),
                ordering = round(ordering, 2),
                total    = round(purchase + holding + waste + stockout + ordering, 2),
                profit   = round(revenue - (purchase + holding + waste + stockout + ordering), 2),
            ))
        return results

    # ── Reorder recommendation ────────────────────────────────────────────────

    def reorder_recommendation(self) -> dict:
        from dexter_inventory.inventory_db import stock_count
        count  = stock_count()
        d      = self.predict_next_day()
        rop_d  = self.rop()
        eoq_d  = self.eoq()
        nv     = self.newsvendor()
        reorder = count <= rop_d['rop']
        qty     = max(0, nv['optimal_qty'] - count) if reorder else 0

        if d > 0:
            days_left = count / d
            if days_left < 1:
                reason = f"CRITICAL: only {count} unit(s) left, ~{days_left:.1f} days stock."
            elif reorder:
                reason = (f"Stock ({count}) below ROP ({rop_d['rop']}). "
                          f"Order {qty} unit(s) — newsvendor Q* = {nv['optimal_qty']}.")
            else:
                reason = (f"Stock OK ({count} units, ~{days_left:.1f} days at "
                          f"{d:.1f}/day demand). ROP={rop_d['rop']}.")
        else:
            reason = "No recent demand data — insufficient history."

        return dict(
            reorder           = reorder,
            order_quantity    = qty,
            current_stock     = count,
            predicted_demand  = round(d, 3),
            rop               = rop_d['rop'],
            eoq               = eoq_d['eoq'],
            newsvendor_q      = nv['optimal_qty'],
            critical_ratio    = nv['critical_ratio'],
            reason            = reason,
            cv                = round(self.cv, 3),
            trained           = self._trained,
            n_days_history    = len(self.series),
            dow_profile       = self.dow_profile(),
            horizon_7d        = self.predict_horizon(7),
            cost_params       = self.cp,
        )

    # ── Legacy shim (used by old web_interface.py) ───────────────────────────

    def summary(self) -> str:
        rec = self.reorder_recommendation()
        if rec['reorder']:
            return (f"⚠ Reorder {rec['order_quantity']} unit(s) — "
                    f"forecast {rec['predicted_demand']:.1f}/day, "
                    f"stock {rec['current_stock']}")
        return (f"Stock OK — forecast {rec['predicted_demand']:.1f}/day, "
                f"stock {rec['current_stock']}")


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    f = DemandForecaster()
    trained = f.train()
    print(f"Model trained: {trained}  (history: {len(f.series)} days)")
    print(f"Predicted demand tomorrow: {f.predict_next_day():.3f}")
    print(f"\nEOQ:  {f.eoq()}")
    print(f"ROP:  {f.rop()}")
    print(f"NV:   {f.newsvendor()}")
    print(f"\nDoW profile:")
    for row in f.dow_profile():
        print(f"  {row['day']}  idx={row['index']:.3f}  demand={row['demand']:.2f}")
    print(f"\n7-day horizon:")
    for row in f.predict_horizon():
        print(f"  {row['date']:18s}  {row['forecast']:.2f}  [{row['lo95']:.2f} – {row['hi95']:.2f}]")
    rec = f.reorder_recommendation()
    print(f"\nReorder needed: {rec['reorder']}")
    print(f"Reason: {rec['reason']}")
