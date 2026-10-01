from __future__ import annotations

import numpy as np
import pytest

from pde_image_denoising.heat import heat_diffusion, heat_step
from pde_image_denoising.perona_malik import (
    conduction_values,
    perona_malik_diffusion,
    perona_malik_step,
)
from pde_image_denoising.verify import (
    discrete_neumann_mode_validation,
    refinement_validation,
)


def _solvers():
    return [
        lambda image, steps: heat_diffusion(image, steps, dt=0.2),
        lambda image, steps: perona_malik_diffusion(
            image, steps, dt=0.2, K=0.1, conduction="exponential"
        ),
        lambda image, steps: perona_malik_diffusion(
            image, steps, dt=0.2, K=0.1, conduction="rational"
        ),
    ]


@pytest.mark.parametrize("solver", _solvers())
def test_constant_images_are_invariant(solver):
    image = np.full((9, 13), 0.37, dtype=np.float64)
    result = solver(image, 12)
    assert np.array_equal(result, image)


@pytest.mark.parametrize("solver", _solvers())
def test_zero_iterations_returns_equal_independent_copy(solver):
    image = np.arange(35, dtype=np.float64).reshape(5, 7) / 35.0
    before = image.copy()
    result = solver(image, 0)
    assert np.array_equal(result, image)
    assert result is not image
    result[0, 0] = -99.0
    assert np.array_equal(image, before)


@pytest.mark.parametrize("solver", _solvers())
def test_shape_finiteness_float64_and_input_nonmutation(solver):
    generator = np.random.default_rng(4)
    image = generator.normal(size=(8, 11))
    before = image.copy()
    result = solver(image, 6)
    assert result.shape == image.shape
    assert result.dtype == np.float64
    assert np.all(np.isfinite(result))
    assert np.array_equal(image, before)


@pytest.mark.parametrize("solver", _solvers())
def test_zero_flux_conserves_mean(solver):
    generator = np.random.default_rng(8)
    image = generator.normal(size=(12, 17))
    result = solver(image, 15)
    assert np.sum(result) == pytest.approx(np.sum(image), abs=2e-13)
    assert np.mean(result) == pytest.approx(np.mean(image), abs=2e-15)


@pytest.mark.parametrize("solver", _solvers())
def test_no_exchange_between_opposite_edges_on_non_square_grid(solver):
    image = np.zeros((5, 9), dtype=np.float64)
    image[2, 0] = 1.0
    result = solver(image, 1)
    assert np.array_equal(result[:, -1], np.zeros(5))
    assert result.shape == (5, 9)


def test_dx_and_dy_are_assigned_to_the_correct_axes():
    image = np.zeros((5, 7), dtype=np.float64)
    image[2, 3] = 1.0
    result = heat_step(image, dt=0.2, dx=2.0, dy=1.0)
    assert result[2, 4] == pytest.approx(0.2 / 4.0)
    assert result[3, 3] == pytest.approx(0.2)


@pytest.mark.parametrize("solver", _solvers())
def test_discrete_maximum_principle_under_cfl(solver):
    generator = np.random.default_rng(12)
    image = generator.normal(size=(14, 10))
    result = solver(image, 20)
    tolerance = 2e-14
    assert np.min(result) >= np.min(image) - tolerance
    assert np.max(result) <= np.max(image) + tolerance


def test_heat_dissipates_squared_l2_distance_to_mean():
    generator = np.random.default_rng(14)
    image = generator.normal(size=(15, 12))
    mean = np.mean(image)
    initial_energy = np.sum((image - mean) ** 2)
    result = heat_diffusion(image, 10, dt=0.2)
    final_energy = np.sum((result - mean) ** 2)
    assert final_energy < initial_energy


def test_heat_matches_independent_discrete_neumann_eigenmode():
    validation = discrete_neumann_mode_validation()
    assert validation["max_abs_error"] < 5e-13


def test_spatial_and_temporal_refinement_are_separated_and_improve():
    validation = refinement_validation()
    assert validation["spatial_error_decreases"]
    assert validation["temporal_error_decreases"]


@pytest.mark.parametrize("name", ["exponential", "rational"])
def test_conduction_values_stay_in_unit_interval(name):
    gradients = np.linspace(0.0, 4.0, 1001)
    values = conduction_values(gradients, K=0.1, conduction=name)
    assert np.all(values >= 0.0)
    assert np.all(values <= 1.0)
    assert values[0] == pytest.approx(1.0)


@pytest.mark.parametrize("name", ["exponential", "rational"])
def test_perona_malik_tends_to_heat_for_large_k(name):
    generator = np.random.default_rng(18)
    image = generator.normal(scale=0.2, size=(9, 13))
    heat = heat_diffusion(image, 5, dt=0.2)
    nonlinear = perona_malik_diffusion(
        image, 5, dt=0.2, K=1e9, conduction=name
    )
    assert np.allclose(nonlinear, heat, rtol=0.0, atol=2e-15)


@pytest.mark.parametrize(
    "kwargs,exception",
    [
        ({"n_steps": -1}, ValueError),
        ({"n_steps": 1.5}, TypeError),
        ({"n_steps": 1, "dt": 0.0}, ValueError),
        ({"n_steps": 1, "dt": 0.251}, ValueError),
        ({"n_steps": 1, "dx": 0.0}, ValueError),
        ({"n_steps": 1, "dy": -1.0}, ValueError),
    ],
)
def test_heat_rejects_invalid_numerical_parameters(kwargs, exception):
    image = np.zeros((4, 5), dtype=np.float64)
    with pytest.raises(exception):
        heat_diffusion(image, **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"K": 0.0},
        {"K": -0.1},
        {"K": np.inf},
        {"conduction": "unknown"},
        {"dt": 0.251},
    ],
)
def test_perona_malik_rejects_invalid_parameters(kwargs):
    image = np.zeros((4, 5), dtype=np.float64)
    parameters = {
        "n_steps": 1,
        "dt": 0.2,
        "K": 0.1,
        "conduction": "exponential",
    }
    parameters.update(kwargs)
    with pytest.raises(ValueError):
        perona_malik_diffusion(image, **parameters)


@pytest.mark.parametrize(
    "bad_image",
    [
        np.zeros((1, 4)),
        np.zeros((4, 1)),
        np.zeros((2, 2, 2)),
        np.array([[0.0, np.nan], [1.0, 2.0]]),
    ],
)
def test_invalid_images_are_rejected(bad_image):
    with pytest.raises(ValueError):
        heat_diffusion(bad_image, 1)


def test_public_steps_do_not_mutate_inputs():
    image = np.arange(30, dtype=np.float64).reshape(5, 6)
    before = image.copy()
    heat_step(image)
    perona_malik_step(image, K=0.2, conduction="rational")
    assert np.array_equal(image, before)
