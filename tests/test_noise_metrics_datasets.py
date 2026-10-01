from __future__ import annotations

import math

import numpy as np
import pytest

from pde_image_denoising.datasets import DATASET_NAMES, get_dataset
from pde_image_denoising.metrics import (
    compute_metrics,
    mean_squared_error,
    peak_signal_to_noise_ratio,
    relative_l2_error,
    structural_similarity_index,
)
from pde_image_denoising.noise import add_gaussian_noise


def test_noise_is_reproducible_for_same_seed_and_differs_for_other_seed():
    image = np.full((16, 17), 0.5)
    first = add_gaussian_noise(image, sigma=0.1, seed=3)
    repeated = add_gaussian_noise(image, sigma=0.1, seed=3)
    other = add_gaussian_noise(image, sigma=0.1, seed=4)
    assert np.array_equal(first, repeated)
    assert not np.array_equal(first, other)


def test_noise_is_not_clipped_to_unit_interval():
    image = np.zeros((32, 32), dtype=np.float64)
    noisy = add_gaussian_noise(image, sigma=1.0, seed=0)
    assert np.min(noisy) < 0.0
    assert np.max(noisy) > 1.0


@pytest.mark.parametrize("sigma", [-1.0, np.inf, np.nan])
def test_invalid_noise_sigma_is_rejected(sigma):
    with pytest.raises(ValueError):
        add_gaussian_noise(np.zeros((4, 4)), sigma=sigma, seed=0)


def test_identical_arrays_have_exact_limit_metrics():
    image = np.linspace(0.0, 1.0, 64).reshape(8, 8)
    metrics = compute_metrics(image, image, data_range=1.0)
    assert metrics["mse"] == 0.0
    assert metrics["relative_l2"] == 0.0
    assert math.isinf(metrics["psnr"]) and metrics["psnr"] > 0
    assert metrics["ssim"] == pytest.approx(1.0)


def test_metrics_match_a_small_hand_calculation():
    truth = np.array([[1.0, 0.0], [0.0, 0.0]])
    estimate = np.zeros((2, 2))
    assert mean_squared_error(truth, estimate) == pytest.approx(0.25)
    assert relative_l2_error(truth, estimate) == pytest.approx(1.0)
    assert peak_signal_to_noise_ratio(truth, estimate, data_range=1.0) == pytest.approx(
        10.0 * math.log10(4.0)
    )


def test_relative_l2_zero_denominator_rule():
    zeros = np.zeros((3, 3))
    assert relative_l2_error(zeros, zeros) == 0.0
    assert math.isinf(relative_l2_error(zeros, np.ones((3, 3))))


def test_ssim_accepts_small_valid_odd_window_and_rejects_too_small():
    image = np.arange(25, dtype=np.float64).reshape(5, 5) / 24.0
    assert structural_similarity_index(image, image) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        structural_similarity_index(np.zeros((2, 2)), np.zeros((2, 2)))


def test_ssim_constant_case_matches_hand_formula():
    zeros = np.zeros((8, 8), dtype=np.float64)
    ones = np.ones((8, 8), dtype=np.float64)
    c1 = 0.01**2
    expected = c1 / (1.0 + c1)
    assert structural_similarity_index(zeros, ones) == pytest.approx(
        expected, rel=0.0, abs=1e-16
    )


def test_ssim_matches_independent_affine_contrast_reference():
    x = np.arange(64, dtype=float).reshape(8, 8) / 63
    y = 0.8 * x + 0.1
    assert structural_similarity_index(x, y, data_range=1.0) == pytest.approx(
        0.975474975647084, rel=0.0, abs=1e-12
    )


def test_ssim_matches_independent_inverted_contrast_reference():
    x = np.arange(64, dtype=float).reshape(8, 8) / 63
    y = 1 - x
    assert structural_similarity_index(x, y, data_range=1.0) == pytest.approx(
        -0.954873020229685, rel=0.0, abs=1e-12
    )


def test_metric_shape_and_range_validation():
    with pytest.raises(ValueError):
        mean_squared_error(np.zeros((3, 3)), np.zeros((3, 4)))
    with pytest.raises(ValueError):
        peak_signal_to_noise_ratio(np.zeros((3, 3)), np.zeros((3, 3)), data_range=0)


@pytest.mark.parametrize("name", DATASET_NAMES)
def test_synthetic_datasets_are_deterministic_float64_and_normalised(name):
    first = get_dataset(name, (31, 47))
    second = get_dataset(name, (31, 47))
    assert np.array_equal(first, second)
    assert first.dtype == np.float64
    assert first.shape == (31, 47)
    assert np.min(first) >= 0.0
    assert np.max(first) <= 1.0
    assert np.std(first) > 0.05


def test_unknown_dataset_and_invalid_shape_are_rejected():
    with pytest.raises(ValueError):
        get_dataset("camera", (16, 16))
    with pytest.raises(ValueError):
        get_dataset("geometric_shapes", (7, 16))
