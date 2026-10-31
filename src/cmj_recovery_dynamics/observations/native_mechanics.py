"""Native measurement arithmetic and public-schedule basis, independently reconstructed.

These deterministic constructors establish neither empirical measurement authority
nor dataset permission. Supplied event times are not inferred from a force signal.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from cmj_recovery_dynamics.contracts import ForecastHorizon
from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    Gate7PublicFeatureRow,
)

NATIVE_MEASUREMENT_VERSION = "gate7_native_measurement_v1"
NATIVE_BASIS_VERSION = "gate7_public_schedule_basis_v1"
NATIVE_BASIS_NAMES = (
    "w2_fast_duration_weighted",
    "w2_slow_duration_weighted",
    "w3_total_dose",
    "w3_fast_increment_weighted",
    "w3_slow_increment_weighted",
)


def _finite(value: float | int | None, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be a finite real number")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must be finite") from error
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


@dataclass(frozen=True, slots=True)
class NativeForceMetrics:
    concentric_duration_s: float
    gross_integral_n_s: float
    net_integral_n_s: float
    force_n_per_kg: float
    net_impulse_m_per_s: float


def native_force_metrics_v1(
    timestamps_s: Sequence[float],
    force_n: Sequence[float],
    *,
    system_mass_kg: float,
    gravity_m_s2: float,
    concentric_onset_s: float,
    takeoff_s: float,
) -> NativeForceMetrics:
    """Integrate the supplied closed contact interval using linear boundaries.

    The caller must separately authenticate event detection, signal calibration,
    system mass and trial validity; no body-mass or event-threshold fallback exists.
    """
    times = tuple(_finite(x, "timestamp") for x in timestamps_s)
    force = tuple(_finite(x, "force") for x in force_n)
    if len(times) != len(force) or len(times) < 2:
        raise ValueError("matching force/time sequences need at least two samples")
    if any(b <= a for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("timestamps must be strictly increasing")
    mass = _finite(system_mass_kg, "system mass")
    gravity = _finite(gravity_m_s2, "gravity")
    start = _finite(concentric_onset_s, "concentric onset")
    end = _finite(takeoff_s, "takeoff")
    if mass <= 0 or gravity <= 0:
        raise ValueError("explicit system mass and gravity must be positive")
    if not times[0] <= start < end <= times[-1]:
        raise ValueError("ordered concentric events must be inside signal support")

    def boundary(event: float) -> float:
        right = bisect_left(times, event)
        if times[right] == event:
            return force[right]
        left = right - 1
        fraction = (event - times[left]) / (times[right] - times[left])
        return force[left] + fraction * (force[right] - force[left])

    support = [(start, boundary(start))]
    support.extend((t, f) for t, f in zip(times, force, strict=True) if start < t < end)
    support.append((end, boundary(end)))
    gross = 0.0
    net = 0.0
    for (left, f_left), (right, f_right) in zip(support, support[1:], strict=False):
        gross += 0.5 * (right - left) * (f_left + f_right)
        net += 0.5 * (right - left) * ((f_left - mass * gravity) + (f_right - mass * gravity))
    duration = end - start
    denominator = mass * duration
    if not math.isfinite(denominator) or denominator <= 0:
        raise ValueError("native force normalization overflowed or underflowed")
    result = NativeForceMetrics(duration, gross, net, gross / denominator, net / mass)
    if not all(
        math.isfinite(x) for x in (gross, net, result.force_n_per_kg, result.net_impulse_m_per_s)
    ):
        raise ValueError("native force mechanics overflowed")
    return result


def gate7_basis_v1(row: Gate7PublicFeatureRow) -> tuple[float, float, float, float, float]:
    """Reconstruct the original unscaled basis from a complete public schedule.

    Only history_exposures and known_plan contribute. The index must appear once
    in known_plan; adding index_exposure separately would double-count it. A true
    known_at_origin flag is an assertion, not independent temporal evidence.
    """
    if type(row) is not Gate7PublicFeatureRow:
        raise TypeError("basis construction needs a Gate7PublicFeatureRow")
    windows = {ForecastHorizon.H72: (66.0, 78.0), ForecastHorizon.D7: (156.0, 180.0)}
    target = _finite(row.target_time_hours, "target time")
    if type(row.horizon) is not ForecastHorizon or row.horizon not in windows:
        raise ValueError("basis requires the registered H72 or D7 horizon")
    low, high = windows[row.horizon]
    if row.target_window_hours != (low, high) or not low <= target <= high:
        raise ValueError("basis target time and window must match horizon")
    if len(row.history_exposures) != 1 or len(row.known_plan) not in (2, 3):
        raise ValueError("basis needs one historical exposure and two/three plan records")
    if _finite(row.index_exposure.time_from_origin_hours, "index time") != 0:
        raise ValueError("index exposure must be at origin")
    index_duration = _finite(row.index_exposure.duration_minutes, "index duration")
    if index_duration < 0:
        raise ValueError("exposure durations must be nonnegative")
    events: list[tuple[float, float]] = []
    for item in row.history_exposures:
        time = _finite(item.time_from_origin_hours, "history time")
        duration = _finite(item.duration_minutes, "history duration")
        if time >= 0 or duration < 0:
            raise ValueError("history must precede origin with nonnegative duration")
        events.append((time, duration / 100.0))
    origin_plans = 0
    for item in row.known_plan:
        time = _finite(item.time_from_origin_hours, "plan time")
        duration = _finite(item.duration_minutes, "plan duration")
        if item.known_at_origin is not True or not 0 <= time <= target or duration < 0:
            raise ValueError("plans must be known at origin, nonnegative and within the query")
        if time == 0:
            origin_plans += 1
            if duration != index_duration:
                raise ValueError("index duration must match the origin plan")
        events.append((time, duration / 100.0))
    if origin_plans != 1 or len({t for t, _ in events}) != len(events):
        raise ValueError("schedule needs distinct event times and exactly one origin plan")
    fast = slow = fast_increment = slow_increment = cumulative = 0.0
    for time, dose in sorted(events):
        fast_weight = float(np.exp(-(max(0.0, target - time) / 36.0)))
        slow_weight = float(np.exp(-(max(0.0, target - time) / 120.0)))
        fast += dose * fast_weight
        slow += dose * slow_weight
        before = 10.0 * cumulative / (1.0 + cumulative) if cumulative else 0.0
        cumulative += dose
        increment = (10.0 * cumulative / (1.0 + cumulative) if cumulative else 0.0) - before
        fast_increment += increment * fast_weight
        slow_increment += increment * slow_weight
    total = 10.0 * cumulative / (1.0 + cumulative) if cumulative else 0.0
    result = (fast, slow, total, fast_increment, slow_increment)
    if not all(math.isfinite(x) for x in result):
        raise ValueError("basis construction overflowed")
    return result
