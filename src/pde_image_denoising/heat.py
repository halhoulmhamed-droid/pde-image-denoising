"""Explicit conservative solver for linear heat diffusion."""

from __future__ import annotations

from time import perf_counter

from numpy.typing import ArrayLike

from .boundaries import (
    FloatArray,
    as_float_image,
    conservative_divergence,
    validate_checkpoints,
    validate_scheme_parameters,
)


def _heat_step_unchecked(
    image: FloatArray, *, dt: float, dx: float, dy: float
) -> FloatArray:
    return image + float(dt) * conservative_divergence(image, dx=dx, dy=dy)


def heat_step(
    image: ArrayLike, *, dt: float = 0.2, dx: float = 1.0, dy: float = 1.0
) -> FloatArray:
    """Advance the heat equation by one explicit Euler step."""
    current = as_float_image(image)
    validate_scheme_parameters(n_steps=1, dt=dt, dx=dx, dy=dy)
    return _heat_step_unchecked(current, dt=dt, dx=dx, dy=dy)


def heat_trajectory(
    image: ArrayLike,
    *,
    checkpoints: tuple[int, ...] | list[int],
    dt: float = 0.2,
    dx: float = 1.0,
    dy: float = 1.0,
    measure_time: bool = True,
) -> tuple[dict[int, FloatArray], dict[int, float]]:
    """Return copied states and cumulative solver times at checkpoints."""
    requested = validate_checkpoints(checkpoints)
    n_steps = requested[-1]
    validate_scheme_parameters(n_steps=n_steps, dt=dt, dx=dx, dy=dy)
    current = as_float_image(image)

    states: dict[int, FloatArray] = {}
    durations: dict[int, float] = {}
    if 0 in requested:
        states[0] = current.copy()
        durations[0] = 0.0

    start = perf_counter()
    requested_set = set(requested)
    for step in range(1, n_steps + 1):
        current = _heat_step_unchecked(current, dt=dt, dx=dx, dy=dy)
        if step in requested_set:
            states[step] = current.copy()
            durations[step] = perf_counter() - start if measure_time else 0.0
    return states, durations


def heat_diffusion(
    image: ArrayLike,
    n_steps: int,
    *,
    dt: float = 0.2,
    dx: float = 1.0,
    dy: float = 1.0,
) -> FloatArray:
    """Diffuse an image for n_steps and return a new float64 array."""
    validate_scheme_parameters(n_steps=n_steps, dt=dt, dx=dx, dy=dy)
    states, _ = heat_trajectory(
        image,
        checkpoints=[int(n_steps)],
        dt=dt,
        dx=dx,
        dy=dy,
        measure_time=False,
    )
    return states[int(n_steps)]
