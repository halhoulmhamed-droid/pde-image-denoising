"""Directional four-neighbour conservative Perona-Malik diffusion."""

from __future__ import annotations

from time import perf_counter

import numpy as np
from numpy.typing import ArrayLike

from .boundaries import (
    FloatArray,
    as_float_image,
    conservative_divergence,
    validate_checkpoints,
    validate_scheme_parameters,
)

CONDUCTION_NAMES = ("exponential", "rational")


def validate_perona_malik_parameters(*, K: float, conduction: str) -> None:
    if not np.isscalar(K) or not np.isfinite(K) or K <= 0:
        raise ValueError("K must be a positive finite scalar")
    if conduction not in CONDUCTION_NAMES:
        raise ValueError(
            f"conduction must be one of {CONDUCTION_NAMES}, received {conduction!r}"
        )


def conduction_values(
    gradient_magnitude: ArrayLike, *, K: float, conduction: str
) -> FloatArray:
    """Evaluate a Perona-Malik conduction law in [0, 1]."""
    validate_perona_malik_parameters(K=K, conduction=conduction)
    magnitude = np.asarray(gradient_magnitude, dtype=np.float64)
    if not np.all(np.isfinite(magnitude)):
        raise ValueError("gradient magnitude must contain only finite values")
    if np.any(magnitude < 0):
        raise ValueError("gradient magnitude must be non-negative")
    ratio_squared = (magnitude / float(K)) ** 2
    if conduction == "exponential":
        values = np.exp(-ratio_squared)
    else:
        values = 1.0 / (1.0 + ratio_squared)
    return np.asarray(values, dtype=np.float64)


def _perona_malik_step_unchecked(
    image: FloatArray,
    *,
    dt: float,
    dx: float,
    dy: float,
    K: float,
    conduction: str,
) -> FloatArray:
    horizontal_gradient = np.abs(image[:, 1:] - image[:, :-1]) / float(dx)
    vertical_gradient = np.abs(image[1:, :] - image[:-1, :]) / float(dy)
    horizontal_conductance = conduction_values(
        horizontal_gradient, K=K, conduction=conduction
    )
    vertical_conductance = conduction_values(
        vertical_gradient, K=K, conduction=conduction
    )
    divergence = conservative_divergence(
        image,
        dx=dx,
        dy=dy,
        horizontal_conductance=horizontal_conductance,
        vertical_conductance=vertical_conductance,
    )
    return image + float(dt) * divergence


def perona_malik_step(
    image: ArrayLike,
    *,
    dt: float = 0.2,
    dx: float = 1.0,
    dy: float = 1.0,
    K: float = 0.1,
    conduction: str = "exponential",
) -> FloatArray:
    """Advance the directional Perona-Malik scheme by one Euler step."""
    current = as_float_image(image)
    validate_scheme_parameters(n_steps=1, dt=dt, dx=dx, dy=dy)
    validate_perona_malik_parameters(K=K, conduction=conduction)
    return _perona_malik_step_unchecked(
        current, dt=dt, dx=dx, dy=dy, K=K, conduction=conduction
    )


def perona_malik_trajectory(
    image: ArrayLike,
    *,
    checkpoints: tuple[int, ...] | list[int],
    dt: float = 0.2,
    dx: float = 1.0,
    dy: float = 1.0,
    K: float = 0.1,
    conduction: str = "exponential",
    measure_time: bool = True,
) -> tuple[dict[int, FloatArray], dict[int, float]]:
    """Return copied states and cumulative solver times at checkpoints."""
    requested = validate_checkpoints(checkpoints)
    n_steps = requested[-1]
    validate_scheme_parameters(n_steps=n_steps, dt=dt, dx=dx, dy=dy)
    validate_perona_malik_parameters(K=K, conduction=conduction)
    current = as_float_image(image)

    states: dict[int, FloatArray] = {}
    durations: dict[int, float] = {}
    if 0 in requested:
        states[0] = current.copy()
        durations[0] = 0.0

    start = perf_counter()
    requested_set = set(requested)
    for step in range(1, n_steps + 1):
        current = _perona_malik_step_unchecked(
            current, dt=dt, dx=dx, dy=dy, K=K, conduction=conduction
        )
        if step in requested_set:
            states[step] = current.copy()
            durations[step] = perf_counter() - start if measure_time else 0.0
    return states, durations


def perona_malik_diffusion(
    image: ArrayLike,
    n_steps: int,
    *,
    dt: float = 0.2,
    dx: float = 1.0,
    dy: float = 1.0,
    K: float = 0.1,
    conduction: str = "exponential",
) -> FloatArray:
    """Diffuse an image and return a new float64 array."""
    validate_scheme_parameters(n_steps=n_steps, dt=dt, dx=dx, dy=dy)
    validate_perona_malik_parameters(K=K, conduction=conduction)
    states, _ = perona_malik_trajectory(
        image,
        checkpoints=[int(n_steps)],
        dt=dt,
        dx=dx,
        dy=dy,
        K=K,
        conduction=conduction,
        measure_time=False,
    )
    return states[int(n_steps)]
