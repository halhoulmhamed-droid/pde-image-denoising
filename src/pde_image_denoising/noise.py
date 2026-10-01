"""Deterministic Gaussian-noise generation without clipping."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .boundaries import FloatArray, as_float_image


def add_gaussian_noise(
    image: ArrayLike, *, sigma: float, seed: int
) -> FloatArray:
    """Add independent centred Gaussian noise using a local RNG."""
    clean = as_float_image(image)
    if not np.isscalar(sigma) or not np.isfinite(sigma) or sigma < 0:
        raise ValueError("sigma must be a non-negative finite scalar")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    generator = np.random.default_rng(int(seed))
    noise = generator.normal(0.0, float(sigma), size=clean.shape)
    return np.asarray(clean + noise, dtype=np.float64)
