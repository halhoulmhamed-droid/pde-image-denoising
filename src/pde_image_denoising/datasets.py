"""Synthetic, dependency-free clean images used by the quick protocol."""

from __future__ import annotations

import numpy as np

from .boundaries import FloatArray

DATASET_NAMES = ("geometric_shapes", "ramps_and_edges")


def _validate_shape(shape: tuple[int, int] | list[int]) -> tuple[int, int]:
    if len(shape) != 2:
        raise ValueError("image shape must have two entries")
    height, width = shape
    if (
        isinstance(height, bool)
        or isinstance(width, bool)
        or not isinstance(height, (int, np.integer))
        or not isinstance(width, (int, np.integer))
        or height < 8
        or width < 8
    ):
        raise ValueError("synthetic images require integer dimensions >= 8")
    return int(height), int(width)


def geometric_shapes(shape: tuple[int, int] | list[int]) -> FloatArray:
    """Piecewise-constant regions containing a rectangle and a disk."""
    height, width = _validate_shape(shape)
    rows, columns = np.indices((height, width), dtype=np.float64)
    image = np.full((height, width), 0.15, dtype=np.float64)
    image[:, width // 2 :] = 0.32
    image[height // 6 : height // 2, width // 10 : 2 * width // 5] = 0.72
    centre_y, centre_x = 2.0 * height / 3.0, 3.0 * width / 4.0
    radius = min(height, width) / 6.0
    disk = (rows - centre_y) ** 2 + (columns - centre_x) ** 2 <= radius**2
    image[disk] = 0.92
    return image


def ramps_and_edges(shape: tuple[int, int] | list[int]) -> FloatArray:
    """Smooth ramp plus curved and oblique discontinuities."""
    height, width = _validate_shape(shape)
    rows, columns = np.indices((height, width), dtype=np.float64)
    x = columns / float(width - 1)
    y = rows / float(height - 1)
    image = 0.08 + 0.48 * x
    image = image + 0.16 * (y >= 0.55)
    ellipse = ((x - 0.28) / 0.16) ** 2 + ((y - 0.70) / 0.18) ** 2 <= 1.0
    image[ellipse] = 0.88
    diagonal = np.abs(y - (0.12 + 0.68 * x)) <= 0.025
    image[diagonal] = 0.04
    return np.asarray(np.clip(image, 0.0, 1.0), dtype=np.float64)


def get_dataset(name: str, shape: tuple[int, int] | list[int]) -> FloatArray:
    """Generate a named clean synthetic image."""
    if name == "geometric_shapes":
        return geometric_shapes(shape)
    if name == "ramps_and_edges":
        return ramps_and_edges(shape)
    raise ValueError(f"unknown dataset {name!r}; expected one of {DATASET_NAMES}")
