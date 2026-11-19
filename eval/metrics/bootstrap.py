"""Utterance-level and paired bootstrap confidence intervals (§11.3)."""
from __future__ import annotations

import random
from typing import Callable, Sequence

DEFAULT_RESAMPLES = 10_000
SEED = 20261119


def percentile_ci(values: Sequence[float], alpha: float = 0.05) -> tuple[float, float]:
    ordered = sorted(values)
    lo = max(0, int(round((alpha / 2) * len(ordered))) - 1)
    hi = min(len(ordered) - 1, int(round((1 - alpha / 2) * len(ordered))))
    return ordered[lo], ordered[hi]


def bootstrap_metric(values: Sequence[float], statistic: Callable[[Sequence[float]], float] | None = None,
                     resamples: int = DEFAULT_RESAMPLES, seed: int = SEED) -> dict:
    """Percentile 95% CI for a metric computed over utterance-level values."""
    if not values:
        return {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "resamples": 0}
    stat = statistic or (lambda xs: sum(xs) / len(xs))
    rng = random.Random(seed)
    n = len(values)
    boots = [stat([values[rng.randrange(n)] for _ in range(n)]) for _ in range(resamples)]
    low, high = percentile_ci(boots)
    return {"mean": round(stat(values), 4), "ci_low": round(low, 4),
            "ci_high": round(high, 4), "resamples": resamples, "seed": seed}


def paired_bootstrap(a: Sequence[float], b: Sequence[float],
                     resamples: int = DEFAULT_RESAMPLES, seed: int = SEED) -> dict:
    """Paired bootstrap of the difference (a - b) on matched utterances."""
    if len(a) != len(b) or not a:
        return {"difference": 0.0, "ci_low": 0.0, "ci_high": 0.0, "significant": False}
    rng = random.Random(seed)
    n = len(a)
    deltas = [x - y for x, y in zip(a, b)]
    boots = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        boots.append(sum(deltas[i] for i in idx) / n)
    low, high = percentile_ci(boots)
    diff = sum(deltas) / n
    return {"difference": round(diff, 4), "ci_low": round(low, 4),
            "ci_high": round(high, 4), "significant": (low > 0 or high < 0),
            "resamples": resamples, "seed": seed}
