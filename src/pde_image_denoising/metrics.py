"""Image-fidelity metrics with an explicit unit data range."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike

from .boundaries import FloatArray


def _pair(reference: ArrayLike, estimate: ArrayLike) -> tuple[FloatArray, FloatArray]:
    truth = np.asarray(reference, dtype=np.float64)
    result = np.asarray(estimate, dtype=np.float64)
    if truth.shape != result.shape:
        raise ValueError("reference and estimate must have identical shapes")
    if truth.ndim != 2:
        raise ValueError("metrics expect two-dimensional grayscale arrays")
    if not np.all(np.isfinite(truth)) or not np.all(np.isfinite(result)):
        raise ValueError("metrics expect finite arrays")
    return truth, result


def mean_squared_error(reference: ArrayLike, estimate: ArrayLike) -> float:
    truth, result = _pair(reference, estimate)
    return float(np.mean((truth - result) ** 2, dtype=np.float64))


def relative_l2_error(reference: ArrayLike, estimate: ArrayLike) -> float:
    truth, result = _pair(reference, estimate)
    denominator = float(np.linalg.norm(truth.ravel()))
    numerator = float(np.linalg.norm((truth - result).ravel()))
    if denominator == 0.0:
        return 0.0 if numerator == 0.0 else math.inf
    return numerator / denominator


def peak_signal_to_noise_ratio(
    reference: ArrayLike, estimate: ArrayLike, *, data_range: float = 1.0
) -> float:
    if not np.isfinite(data_range) or data_range <= 0:
        raise ValueError("data_range must be a positive finite scalar")
    error = mean_squared_error(reference, estimate)
    if error == 0.0:
        return math.inf
    return 10.0 * math.log10(float(data_range) ** 2 / error)


def structural_similarity_index(
    reference: ArrayLike, estimate: ArrayLike, *, data_range: float = 1.0
) -> float:
    """Mean local SSIM with a uniform window and sample covariances.

    This NumPy implementation uses K1=0.01, K2=0.03 and the standard
    luminance/contrast-structure formula. Only valid windows are averaged, so
    no padding convention enters the reported scalar.
    """
    truth, result = _pair(reference, estimate)
    if not np.isfinite(data_range) or data_range <= 0:
        raise ValueError("data_range must be a positive finite scalar")
    minimum_size = min(truth.shape)
    if minimum_size < 3:
        raise ValueError("SSIM requires each image dimension to be at least 3")
    window_size = 7 if minimum_size >= 7 else minimum_size
    if window_size % 2 == 0:
        window_size -= 1
    sample_count = window_size**2

    def valid_box_mean(array: FloatArray) -> FloatArray:
        integral = np.pad(
            array, ((1, 0), (1, 0)), mode="constant", constant_values=0.0
        )
        integral = np.cumsum(np.cumsum(integral, axis=0), axis=1)
        sums = (
            integral[window_size:, window_size:]
            - integral[:-window_size, window_size:]
            - integral[window_size:, :-window_size]
            + integral[:-window_size, :-window_size]
        )
        return sums / float(sample_count)

    truth_mean = valid_box_mean(truth)
    result_mean = valid_box_mean(result)
    covariance_normalisation = sample_count / float(sample_count - 1)
    truth_variance = covariance_normalisation * (
        valid_box_mean(truth * truth) - truth_mean**2
    )
    result_variance = covariance_normalisation * (
        valid_box_mean(result * result) - result_mean**2
    )
    covariance = covariance_normalisation * (
        valid_box_mean(truth * result) - truth_mean * result_mean
    )
    # Integral-image cancellation can create tiny negative variances.
    truth_variance = np.maximum(truth_variance, 0.0)
    result_variance = np.maximum(result_variance, 0.0)

    c1 = (0.01 * float(data_range)) ** 2
    c2 = (0.03 * float(data_range)) ** 2
    numerator = (2.0 * truth_mean * result_mean + c1) * (
        2.0 * covariance + c2
    )
    denominator = (truth_mean**2 + result_mean**2 + c1) * (
        truth_variance + result_variance + c2
    )
    return float(np.mean(numerator / denominator, dtype=np.float64))


def compute_metrics(
    reference: ArrayLike, estimate: ArrayLike, *, data_range: float = 1.0
) -> dict[str, float]:
    """Compute all required deterministic metrics."""
    return {
        "mse": mean_squared_error(reference, estimate),
        "relative_l2": relative_l2_error(reference, estimate),
        "psnr": peak_signal_to_noise_ratio(
            reference, estimate, data_range=data_range
        ),
        "ssim": structural_similarity_index(
            reference, estimate, data_range=data_range
        ),
    }
