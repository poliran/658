"""Randomness and baseline statistical tests for lottery draws.

Provides chi-squared uniformity test, runs test, serial correlation, and compression-based audit.
"""
from typing import Dict, Iterable, List
import numpy as np
import zlib
import logging

log = logging.getLogger(__name__)


def chi_squared_uniformity(draws: Iterable[Iterable[int]], num_bins: int) -> Dict[str, float]:
    """Chi-squared test for uniformity over integer bins 1..num_bins.

    Returns statistic, degrees of freedom and p-value if scipy is available (else None).
    """
    counts = np.zeros(num_bins, dtype=int)
    total = 0
    for draw in draws:
        for n in draw:
            if 1 <= n <= num_bins:
                counts[n - 1] += 1
                total += 1
    expected = total / float(num_bins) if num_bins > 0 else 0
    # chi2 statistic
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.sum((counts - expected) ** 2 / (expected + 1e-12))
    dof = num_bins - 1
    p_value = None
    try:
        from scipy.stats import chi2 as _chi2

        p_value = 1.0 - _chi2.cdf(chi2, dof)
    except Exception:
        log.debug("scipy not available; returning chi2 statistic without p-value")
    return {"chi2": float(chi2), "dof": int(dof), "p_value": p_value}


def runs_test_median(sequence: Iterable[int]) -> Dict[str, float]:
    """Runs test above/below median for a sequence of integers.

    Returns z-score and two-sided p-value (normal approximation).
    """
    arr = np.asarray(list(sequence))
    if arr.size == 0:
        return {"z": float("nan"), "p_value": None}
    med = np.median(arr)
    signs = arr > med
    n1 = np.sum(signs)
    n2 = len(arr) - n1
    runs = 1
    for i in range(1, len(signs)):
        if signs[i] != signs[i - 1]:
            runs += 1
    # expected runs and variance under null
    if n1 == 0 or n2 == 0:
        return {"z": float("nan"), "p_value": None}
    expected_runs = 1 + 2.0 * n1 * n2 / (n1 + n2)
    var_runs = (2.0 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / (((n1 + n2) ** 2) * (n1 + n2 - 1))
    z = (runs - expected_runs) / np.sqrt(var_runs) if var_runs > 0 else float("nan")
    # two-sided p-value from normal approx
    p_value = 2.0 * (1.0 - 0.5 * (1.0 + np.math.erf(abs(z) / np.sqrt(2.0)))) if not np.isnan(z) else None
    return {"runs": int(runs), "expected_runs": float(expected_runs), "z": float(z), "p_value": p_value}


def serial_correlation(sequence: Iterable[int], lag: int = 1) -> Dict[str, float]:
    """Compute lag-k serial autocorrelation for a flattened sequence.

    Returns autocorrelation coefficient.
    """
    arr = np.asarray(list(sequence), dtype=float)
    n = len(arr)
    if n <= lag:
        return {"lag": int(lag), "autocorr": float("nan")}
    arr_mean = np.mean(arr)
    num = np.sum((arr[:-lag] - arr_mean) * (arr[lag:] - arr_mean))
    den = np.sum((arr - arr_mean) ** 2)
    autocorr = float(num / den) if den != 0 else float("nan")
    return {"lag": int(lag), "autocorr": autocorr}


def compression_audit(draws: Iterable[Iterable[int]]) -> Dict[str, float]:
    """Compression-based randomness audit using zlib compression ratio.

    Flattens numbers into bytes and returns compression ratio (compressed / raw).
    Lower ratio indicates more compressible (less random).
    """
    flat = []
    for draw in draws:
        for n in draw:
            flat.append(int(n))
    if not flat:
        return {"ratio": float("nan"), "raw_bytes": 0, "compressed_bytes": 0}
    # represent as bytes: each number as 2-byte big-endian
    raw = b"".join(int(n).to_bytes(2, byteorder="big", signed=False) for n in flat)
    compressed = zlib.compress(raw)
    raw_size = len(raw)
    comp_size = len(compressed)
    ratio = float(comp_size) / float(raw_size) if raw_size > 0 else float("nan")
    return {"ratio": ratio, "raw_bytes": raw_size, "compressed_bytes": comp_size}


def analyze_draws(draws: Iterable[Iterable[int]], num_bins: int = 58) -> Dict[str, object]:
    """Run all randomness audits on the provided draws.

    draws: iterable of draws, each draw is an iterable of integers (1..num_bins)
    """
    draws_list: List[List[int]] = [list(d) for d in draws]
    flattened = [n for draw in draws_list for n in draw]
    return {
        "chi2": chi_squared_uniformity(draws_list, num_bins),
        "runs": runs_test_median(flattened),
        "serial_corr_lag1": serial_correlation(flattened, lag=1),
        "compression": compression_audit(draws_list),
    }
