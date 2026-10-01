from __future__ import annotations

import csv
import json
import numpy as np
import pytest

from pde_image_denoising import verify
from pde_image_denoising.experiments import (
    METRICS_FIELDS,
    SUMMARY_FIELDS,
    SUMMARY_GROUP_FIELDS,
    SUMMARY_VALUE_FIELDS,
    array_sha256,
    compute_experiment,
    summarise_records,
)


def _write_rows(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path):
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


@pytest.fixture
def verification_case(tmp_path):
    """Small deterministic CSV/array fixture, with synthetic recorded timings."""
    config = {
        "experiment_name": "quick",
        "output_dir": "unused",
        "image_shape": [8, 8],
        "images": ["geometric_shapes"],
        "sigmas": [0.05],
        "seeds": [0, 1],
        "dx": 1.0,
        "dy": 1.0,
        "dt": 0.2,
        "checkpoints": [0, 1],
        "perona_malik": {
            "conductions": ["exponential", "rational"],
            "K_values": [0.1],
        },
        "representative": {
            "image": "geometric_shapes",
            "sigma": 0.05,
            "seed": 0,
            "checkpoint": 1,
            "K": 0.1,
        },
        "data_range": 1.0,
    }
    data = compute_experiment(config, measure_time=False)
    for row in data.records:
        if row["n"] > 0:
            # Deliberately unrelated to a real timer: verification must use CSV.
            row["duration_seconds"] = 2.0 + row["seed"]
    directory = tmp_path / "quick"
    for name in ("arrays", "tables", "figures"):
        (directory / name).mkdir(parents=True, exist_ok=True)
    _write_rows(directory / "metrics.csv", METRICS_FIELDS, data.records)
    _write_rows(
        directory / "summary.csv", SUMMARY_FIELDS, summarise_records(data.records)
    )
    (directory / "config_used.json").write_text(json.dumps(config), encoding="utf-8")
    (directory / "environment.json").write_text("{}", encoding="utf-8")
    (directory / "run.log").write_text("unit-test fixture\n", encoding="utf-8")
    (directory / "tables" / "quick_summary.tex").write_text(
        "% fixture: plotting is not exercised by these verifier tests\n",
        encoding="utf-8",
    )
    # The verifier checks presence, not image rendering. Test fixtures are local.
    for stem in (
        "comparison", "metric_curves", "k_comparison",
        "intensity_profile", "gradient_maps",
    ):
        for extension in ("png", "pdf"):
            (directory / "figures" / f"{stem}.{extension}").touch()
    np.savez_compressed(directory / "arrays" / "inputs.npz", **data.input_arrays)
    np.savez_compressed(
        directory / "arrays" / "representative_outputs.npz",
        **data.representative_arrays,
    )
    return directory, config


def test_strict_verifier_checks_summary_and_recorded_duration_statistics(verification_case):
    directory, _ = verification_case
    result = verify.verify_results(directory)
    assert result["verification_mode"] == "strict"
    assert result["tolerances"] == {"rtol": 0.0, "atol": 0.0}
    assert result["exact_reproduction"]
    assert result["summary_groups_checked"] == 7
    assert result["summary_statistics_checked"] == 70
    assert result["duration_statistics_checked_from_recorded_values"]
    assert not result["duration_columns_compared"]
    assert result["recomputed_output_hash_differences"] == []


@pytest.mark.parametrize(
    "column",
    [
        f"{field}_{statistic}"
        for field in SUMMARY_VALUE_FIELDS
        for statistic in ("mean", "std")
    ],
)
@pytest.mark.parametrize("mode", verify.VERIFICATION_MODES)
def test_verifier_rejects_each_altered_summary_statistic(verification_case, column, mode):
    directory, _ = verification_case
    rows = _read_rows(directory / "summary.csv")
    rows[0][column] = float(rows[0][column]) + 0.01
    _write_rows(directory / "summary.csv", SUMMARY_FIELDS, rows)
    with pytest.raises(AssertionError, match=column):
        verify.verify_results(directory, mode=mode)


@pytest.mark.parametrize("mode", verify.VERIFICATION_MODES)
@pytest.mark.parametrize("mutation", ["schema", "group", "duplicate_group", "n_seeds"])
def test_summary_structure_is_exact_in_both_modes(verification_case, mode, mutation):
    directory, _ = verification_case
    rows = _read_rows(directory / "summary.csv")
    fields = list(SUMMARY_FIELDS)
    if mutation == "schema":
        fields.reverse()
    elif mutation == "group":
        rows[0]["sigma"] = 0.051
    elif mutation == "duplicate_group":
        for key in SUMMARY_GROUP_FIELDS:
            rows[0][key] = rows[1][key]
    else:
        rows[0]["n_seeds"] = 1
    _write_rows(directory / "summary.csv", fields, rows)
    with pytest.raises(AssertionError):
        verify.verify_results(directory, mode=mode)


@pytest.mark.parametrize("mode", verify.VERIFICATION_MODES)
def test_duplicate_seed_in_metrics_group_is_rejected(verification_case, mode):
    directory, _ = verification_case
    rows = _read_rows(directory / "metrics.csv")
    for row in rows:
        if row["method"] == "noisy" and int(row["seed"]) == 1:
            row["seed"] = 0
            break
    _write_rows(directory / "metrics.csv", METRICS_FIELDS, rows)
    with pytest.raises(AssertionError, match="invalid or duplicate seeds"):
        verify.verify_results(directory, mode=mode)


def test_numerical_rejects_recorded_initial_output_hash_corruption(verification_case):
    directory, _ = verification_case
    rows = _read_rows(directory / "metrics.csv")
    for row in rows:
        if row["method"] == "noisy" and int(row["seed"]) == 1:
            row["output_sha256"] = "0" * 64
            break
    _write_rows(directory / "metrics.csv", METRICS_FIELDS, rows)
    with pytest.raises(AssertionError, match="archived output hash"):
        verify.verify_results(directory, mode="numerical")


def _perturb_recomputation(monkeypatch, *, epsilon):
    original = verify.compute_experiment

    def perturbed(config, *, measure_time):
        assert measure_time is False
        data = original(config, measure_time=measure_time)
        key = "heat_n1"
        data.representative_arrays[key][0, 0] += epsilon
        modified_hash = array_sha256(data.representative_arrays[key])
        for row in data.records:
            if row["method"] == "heat" and row["seed"] == 0 and row["n"] == 1:
                row["mse"] += epsilon
                row["output_sha256"] = modified_hash
        return data

    monkeypatch.setattr(verify, "compute_experiment", perturbed)


def test_numerical_accepts_tiny_recalculation_difference_and_reports_hashes(
    verification_case, monkeypatch
):
    directory, _ = verification_case
    _perturb_recomputation(monkeypatch, epsilon=1e-13)
    result = verify.verify_results(directory, mode="numerical")
    assert result["status"] == "passed"
    assert result["verification_mode"] == "numerical"
    assert result["tolerances"] == {
        "rtol": verify.NUMERICAL_RTOL, "atol": verify.NUMERICAL_ATOL
    }
    assert result["exact_reproduction"] is False
    assert result["archived_array_integrity_exact"]
    assert len(result["recomputed_output_hash_differences"]) == 1
    assert len(result["recomputed_array_hash_differences"]) == 1
    assert (directory / "verification_numerical.json").is_file()
    with pytest.raises(AssertionError):
        verify.verify_results(directory)


def test_numerical_rejects_significant_recalculation_difference(
    verification_case, monkeypatch
):
    directory, _ = verification_case
    _perturb_recomputation(monkeypatch, epsilon=1e-3)
    with pytest.raises(AssertionError, match="mismatch in mse"):
        verify.verify_results(directory, mode="numerical")


@pytest.mark.parametrize("epsilon", [1e-13, 1e-3])
def test_numerical_compares_arrays_independently_of_recorded_metrics(
    verification_case, monkeypatch, epsilon
):
    directory, _ = verification_case
    original = verify.compute_experiment

    def perturbed(config, *, measure_time):
        data = original(config, measure_time=measure_time)
        data.representative_arrays["heat_n1"][0, 0] += epsilon
        return data

    monkeypatch.setattr(verify, "compute_experiment", perturbed)
    if epsilon == 1e-13:
        result = verify.verify_results(directory, mode="numerical")
        assert len(result["recomputed_array_hash_differences"]) == 1
    else:
        with pytest.raises(AssertionError, match="array mismatch"):
            verify.verify_results(directory, mode="numerical")


@pytest.mark.parametrize("key", ["heat_n0", "heat_n1"])
def test_numerical_does_not_tolerate_archived_hash_corruption(verification_case, key):
    directory, _ = verification_case
    path = directory / "arrays" / "representative_outputs.npz"
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    arrays[key][0, 0] += 1e-13
    np.savez_compressed(path, **arrays)
    with pytest.raises(AssertionError, match="archived"):
        verify.verify_results(directory, mode="numerical")


def test_numerical_keeps_input_arrays_exact(verification_case):
    directory, _ = verification_case
    path = directory / "arrays" / "inputs.npz"
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    next(iter(arrays.values()))[0, 0] += 1e-13
    np.savez_compressed(path, **arrays)
    with pytest.raises(AssertionError, match="array mismatch"):
        verify.verify_results(directory, mode="numerical")


def test_verifier_rejects_unknown_mode(verification_case):
    directory, _ = verification_case
    with pytest.raises(ValueError, match="verification mode"):
        verify.verify_results(directory, mode="unknown")


def test_cli_defaults_to_strict_and_requires_explicit_numerical_selection():
    parser = verify.build_parser()
    assert parser.parse_args(["--results", "unused"]).mode == "strict"
    assert parser.parse_args(
        ["--results", "unused", "--mode", "numerical"]
    ).mode == "numerical"
