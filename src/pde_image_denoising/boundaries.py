"""Validation and conservative zero-flux finite-difference operations."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


def as_float_image(image: ArrayLike) -> FloatArray:
    """Return a finite, two-dimensional float64 copy of an image."""
    array = np.asarray(image, dtype=np.float64)
    if array.ndim != 2:
        raise ValueError("image must be a two-dimensional grayscale array")
    if array.shape[0] < 2 or array.shape[1] < 2:
        raise ValueError("image grid must contain at least 2 x 2 pixels")
    if not np.all(np.isfinite(array)):
        raise ValueError("image must contain only finite values")
    return array.copy()


def validate_scheme_parameters(
    *, n_steps: int, dt: float, dx: float, dy: float
) -> None:
    """Validate Euler and grid parameters, including the sufficient CFL bound."""
    if isinstance(n_steps, bool) or not isinstance(n_steps, (int, np.integer)):
        raise TypeError("n_steps must be an integer")
    if n_steps < 0:
        raise ValueError("n_steps must be non-negative")
    for name, value in (("dt", dt), ("dx", dx), ("dy", dy)):
        if not np.isscalar(value) or not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a positive finite scalar")
    cfl = float(dt) * (1.0 / float(dx) ** 2 + 1.0 / float(dy) ** 2)
    tolerance = 32.0 * np.finfo(np.float64).eps
    if cfl > 0.5 + tolerance:
        raise ValueError(
            "explicit step violates dt * (1/dx^2 + 1/dy^2) <= 1/2 "
            f"(received {cfl:.17g})"
        )


def validate_checkpoints(checkpoints: Iterable[int]) -> tuple[int, ...]:
    """Return sorted unique non-negative integer checkpoints."""
    values = tuple(checkpoints)
    if not values:
        raise ValueError("at least one checkpoint is required")
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise TypeError("checkpoints must contain integers")
        if value < 0:
            raise ValueError("checkpoints must be non-negative")
    return tuple(sorted(set(int(value) for value in values)))


def conservative_divergence(
    image: FloatArray,
    *,
    dx: float,
    dy: float,
    horizontal_conductance: FloatArray | None = None,
    vertical_conductance: FloatArray | None = None,
) -> FloatArray:
    """Compute a conservative four-neighbour divergence with no boundary flux.

    Conductances live on interior edges. Each edge contribution is added to one
    incident pixel and subtracted from the other, so the returned array sums to
    zero up to floating-point roundoff.
    """
    horizontal_difference = image[:, 1:] - image[:, :-1]
    vertical_difference = image[1:, :] - image[:-1, :]

    if horizontal_conductance is None:
        horizontal_flux = horizontal_difference / float(dx) ** 2
    else:
        if horizontal_conductance.shape != horizontal_difference.shape:
            raise ValueError("horizontal conductance has an invalid shape")
        horizontal_flux = (
            horizontal_conductance * horizontal_difference / float(dx) ** 2
        )

    if vertical_conductance is None:
        vertical_flux = vertical_difference / float(dy) ** 2
    else:
        if vertical_conductance.shape != vertical_difference.shape:
            raise ValueError("vertical conductance has an invalid shape")
        vertical_flux = vertical_conductance * vertical_difference / float(dy) ** 2

    divergence = np.zeros_like(image, dtype=np.float64)
    divergence[:, :-1] += horizontal_flux
    divergence[:, 1:] -= horizontal_flux
    divergence[:-1, :] += vertical_flux
    divergence[1:, :] -= vertical_flux
    return divergence
