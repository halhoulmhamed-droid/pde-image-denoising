from __future__ import annotations

import copy
import csv
import importlib.metadata
import json

import numpy as np
import pytest

from pde_image_denoising.experiments import (
    compute_experiment,
    environment_metadata,
    expected_row_count,
    expected_summary_count,
    run_and_write,
    summarise_records,
    validate_config,
)
from pde_image_denoising.verify import verify_results


@pytest.fixture
def tiny_config():
    return {
        "experiment_name": "quick",
        "output_dir": "unused-in-test",
        "image_shape": [16, 18],
        "images": ["geometric_shapes"],
        "sigmas": [0.05],
        "seeds": [0, 1],
        "dx": 1.0,
        "dy": 1.0,
        "dt": 0.2,
        "checkpoints": [0, 1, 2],
        "perona_malik": {
            "conductions": ["exponential", "rational"],
            "K_values": [0.05, 0.10],
        },
        "representative": {
            "image": "geometric_shapes",
            "sigma": 0.05,
            "seed": 0,
            "checkpoint": 2,
            "K": 0.10,
        },
        "data_range": 1.0,
    }


def _without_durations(records):
    return [
        {key: value for key, value in row.items() if key != "duration_seconds"}
        for row in records
    ]


def test_repeated_experiment_reproduces_arrays_and_metrics(tiny_config):
    first = compute_experiment(tiny_config, measure_time=False)
    second = compute_experiment(tiny_config, measure_time=False)
    assert _without_durations(first.records) == _without_durations(second.records)
    assert set(first.input_arrays) == set(second.input_arrays)
    assert set(first.representative_arrays) == set(second.representative_arrays)
    for key in first.input_arrays:
        assert np.array_equal(first.input_arrays[key], second.input_arrays[key])
    for key in first.representative_arrays:
        assert np.array_equal(
            first.representative_arrays[key], second.representative_arrays[key]
        )


def test_every_method_reuses_one_noisy_array_per_observation(tiny_config):
    data = compute_experiment(tiny_config, measure_time=False)
    hashes = {}
    for row in data.records:
        key = (row["image"], row["sigma"], row["seed"])
        hashes.setdefault(key, set()).add(row["noisy_sha256"])
    assert len(hashes) == 2
    assert all(len(values) == 1 for values in hashes.values())


def test_expected_counts_and_seed_summary(tiny_config):
    data = compute_experiment(tiny_config, measure_time=False)
    summary = summarise_records(data.records)
    assert len(data.records) == expected_row_count(tiny_config) == 32
    assert len(summary) == expected_summary_count(tiny_config) == 16
    assert {row["n_seeds"] for row in summary} == {2}


def test_full_tiny_write_and_verify_pipeline(tmp_path, tiny_config):
    destination = tmp_path / "quick"
    outcome = run_and_write(tiny_config, destination)
    assert outcome["metrics_rows"] == 32
    assert outcome["summary_rows"] == 16
    verification = verify_results(destination)
    assert verification["status"] == "passed"
    assert verification["deterministic_columns_recomputed"]
    assert verification["shared_noisy_observations"] == 2
    with (destination / "metrics.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        assert len(list(csv.DictReader(stream))) == 32
    stored = json.loads((destination / "verification.json").read_text("utf-8"))
    assert stored["status"] == "passed"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda config: config.update(experiment_name="full"),
        lambda config: config.update(data_range=2.0),
        lambda config: config.update(dt=0.3),
        lambda config: config.update(checkpoints=[1, 2]),
        lambda config: config["perona_malik"].update(K_values=[0.0]),
        lambda config: config["perona_malik"].update(conductions=["bad"]),
        lambda config: config.update(images=["camera"]),
        lambda config: config.update(seeds=[0, 0]),
        lambda config: config.update(seeds=[0, -1]),
        lambda config: config.update(sigmas=[0.05, 0.05]),
        lambda config: config["perona_malik"].update(K_values=[0.05, 0.05]),
    ],
)
def test_invalid_quick_configurations_are_rejected(tiny_config, mutation):
    invalid = copy.deepcopy(tiny_config)
    mutation(invalid)
    with pytest.raises(ValueError):
        validate_config(invalid)


def test_environment_metadata_handles_optional_pytest_absence(monkeypatch):
    def version_without_pytest(distribution):
        if distribution == "pytest":
            raise importlib.metadata.PackageNotFoundError(distribution)
        return "test-version"

    monkeypatch.setattr(importlib.metadata, "version", version_without_pytest)
    metadata = environment_metadata()
    assert metadata["packages"]["pytest"] == "not installed"
    assert metadata["packages"]["pde-image-denoising"] == "test-version"
