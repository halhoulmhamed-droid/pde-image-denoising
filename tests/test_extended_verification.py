"""Independent corruption checks for extended artifacts and external reports."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from pde_image_denoising import verify
from pde_image_denoising.experiments import (
    METRICS_FIELDS,
    SUMMARY_FIELDS,
    compute_experiment,
    expected_row_count,
    expected_summary_count,
    load_config,
    summarise_records,
)


def _write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_manifest(directory, config):
    files = [
        {
            "path": path.relative_to(directory).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(directory.rglob("*"))
        if path.is_file()
        and path.name not in {
            "manifest.json", "verification.json", "verification_numerical.json"
        }
    ]
    payload = {
        "experiment_name": config["experiment_name"],
        "config_sha256": hashlib.sha256(
            (directory / "config_used.json").read_bytes()
        ).hexdigest(),
        "files": files,
    }
    (directory / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    return payload


@pytest.fixture
def small_results(tmp_path):
    """8x8 fixture: no plotting, measured timings, or extended-scale computation."""
    def create(name):
        config = {
            "experiment_name": name,
            "output_dir": "unused",
            "image_shape": [8, 8],
            "images": ["geometric_shapes"],
            "sigmas": [0.1],
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
                "image": "geometric_shapes", "sigma": 0.1,
                "seed": 0, "checkpoint": 1, "K": 0.1,
            },
            "data_range": 1.0,
        }
        data = compute_experiment(config, measure_time=False)
        directory = tmp_path / name
        for subdirectory in ("arrays", "figures", "tables"):
            (directory / subdirectory).mkdir(parents=True)
        _write_csv(directory / "metrics.csv", METRICS_FIELDS, data.records)
        _write_csv(
            directory / "summary.csv", SUMMARY_FIELDS, summarise_records(data.records)
        )
        (directory / "config_used.json").write_text(json.dumps(config), encoding="utf-8")
        (directory / "environment.json").write_text("{}\n", encoding="utf-8")
        (directory / "run.log").write_text(f"experiment={name}\n", encoding="utf-8")
        table = "quick_summary.tex" if name == "quick" else "representative_summary.tex"
        (directory / "tables" / table).write_text("% test fixture\n", encoding="utf-8")
        for stem in (
            "comparison", "metric_curves", "k_comparison",
            "intensity_profile", "gradient_maps",
        ):
            for extension in ("png", "pdf"):
                # Presence/integrity fixtures do not assert valid rendered images.
                (directory / "figures" / f"{stem}.{extension}").write_bytes(b"fixture")
        np.savez_compressed(directory / "arrays" / "inputs.npz", **data.input_arrays)
        np.savez_compressed(
            directory / "arrays" / "representative_outputs.npz",
            **data.representative_arrays,
        )
        if name == "extended":
            (directory / "analysis.json").write_text("{}\n", encoding="utf-8")
            for filename in (
                "extended_common_checkpoints.csv", "extended_common_checkpoints.tex",
                "oracle_exploratory.csv", "oracle_exploratory.tex",
            ):
                (directory / "tables" / filename).write_text("fixture\n", encoding="utf-8")
            for kind in ("metric_curves", "k_sensitivity"):
                for extension in ("png", "pdf"):
                    path = directory / "figures" / (
                        f"{kind}_geometric_shapes_sigma0p1.{extension}"
                    )
                    path.write_bytes(b"fixture")
            _write_manifest(directory, config)
        return directory, config
    return create


def test_frozen_extended_config_counts():
    config = load_config(Path(__file__).resolve().parents[1] / "configs" / "extended.json")
    assert config["experiment_name"] == "extended"
    assert expected_row_count(config) == 4380
    assert expected_summary_count(config) == 438
    assert len(config["images"]) * len(config["sigmas"]) * len(config["seeds"]) == 60
    assert config["seeds"] == list(range(10))
    assert config["representative"] == {
        "image": "geometric_shapes", "sigma": 0.1,
        "seed": 0, "checkpoint": 20, "K": 0.1,
    }


@pytest.mark.parametrize("mode", verify.VERIFICATION_MODES)
def test_extended_manifest_and_reproduction_in_both_modes(small_results, mode):
    directory, _ = small_results("extended")
    outcome = verify.verify_results(directory, mode=mode)
    assert outcome["status"] == "passed"
    assert outcome["experiment_name"] == "extended"
    assert outcome["manifest_integrity_exact"]
    assert outcome["manifest_files_checked"] == 27
    assert outcome["shared_noisy_observations"] == 2
    assert outcome["metrics_rows"] == 14
    assert outcome["summary_groups_checked"] == 7


@pytest.mark.parametrize("mode", verify.VERIFICATION_MODES)
@pytest.mark.parametrize(
    "relative", ["analysis.json", "tables/extended_common_checkpoints.csv", "figures/comparison.png"]
)
def test_extended_verifier_rejects_artifact_integrity_changes(small_results, relative, mode):
    directory, _ = small_results("extended")
    (directory / relative).write_bytes(b"altered")
    with pytest.raises(AssertionError, match="manifest integrity mismatch"):
        verify.verify_results(directory, mode=mode)


@pytest.mark.parametrize("mode", verify.VERIFICATION_MODES)
@pytest.mark.parametrize(
    "relative",
    [
        "tables/oracle_exploratory.tex",
        "figures/metric_curves_geometric_shapes_sigma0p1.png",
        "figures/metric_curves_geometric_shapes_sigma0p1.pdf",
        "figures/k_sensitivity_geometric_shapes_sigma0p1.png",
        "figures/k_sensitivity_geometric_shapes_sigma0p1.pdf",
    ],
)
def test_extended_requires_each_case_figure_pair_and_oracle_table(
    small_results, relative, mode
):
    directory, config = small_results("extended")
    # The omitted fixture file is absent even from an internally consistent
    # rebuilt manifest; the protocol must still require it explicitly.
    (directory / relative).unlink()
    _write_manifest(directory, config)
    with pytest.raises(FileNotFoundError, match="missing extended artifacts"):
        verify.verify_results(directory, mode=mode)


@pytest.mark.parametrize("mutation", ["experiment", "config_hash", "schema", "duplicate", "size", "digest"])
def test_extended_verifier_rejects_manifest_corruption(small_results, mutation):
    directory, _ = small_results("extended")
    path = directory / "manifest.json"
    manifest = json.loads(path.read_text("utf-8"))
    if mutation == "experiment":
        manifest["experiment_name"] = "quick"
    elif mutation == "config_hash":
        manifest["config_sha256"] = "0" * 64
    elif mutation == "schema":
        manifest["unexpected"] = True
    elif mutation == "duplicate":
        manifest["files"].append(dict(manifest["files"][0]))
    elif mutation == "size":
        manifest["files"][0]["size_bytes"] += 1
    else:
        manifest["files"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AssertionError, match="manifest"):
        verify.verify_results(directory)


@pytest.mark.parametrize("relative", ["../outside.json", "C:/outside.json", "/outside.json", "figures\\comparison.png"])
def test_extended_verifier_rejects_unsafe_manifest_paths(small_results, relative):
    directory, _ = small_results("extended")
    path = directory / "manifest.json"
    manifest = json.loads(path.read_text("utf-8"))
    manifest["files"][0]["path"] = relative
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AssertionError, match="unsafe or reserved manifest path"):
        verify.verify_results(directory)


@pytest.mark.parametrize("mutation", ["extra", "omitted", "missing"])
def test_extended_manifest_requires_complete_inventory(small_results, mutation):
    directory, _ = small_results("extended")
    path = directory / "manifest.json"
    manifest = json.loads(path.read_text("utf-8"))
    if mutation == "extra":
        (directory / "tables" / "unlisted.csv").write_text("extra\n", encoding="utf-8")
    elif mutation == "omitted":
        manifest["files"] = [item for item in manifest["files"] if item["path"] != "analysis.json"]
        path.write_text(json.dumps(manifest), encoding="utf-8")
    else:
        # A manifest cannot claim a file absent from the temporary fixture.
        manifest["files"].append({"path": "tables/missing.csv", "sha256": "0" * 64, "size_bytes": 0})
        path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AssertionError, match="manifest"):
        verify.verify_results(directory)


def test_extended_log_must_identify_experiment(small_results):
    directory, config = small_results("extended")
    (directory / "run.log").write_text("experiment=quick\n", encoding="utf-8")
    _write_manifest(directory, config)
    with pytest.raises(AssertionError, match="run.log"):
        verify.verify_results(directory)


@pytest.mark.parametrize("mode", verify.VERIFICATION_MODES)
def test_explicit_quick_report_preserves_every_existing_result_file(small_results, tmp_path, mode):
    directory, _ = small_results("quick")
    old_report = directory / (
        "verification.json" if mode == "strict" else "verification_numerical.json"
    )
    old_report.write_text('{"historical_report": true}\n', encoding="utf-8")
    before = {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*") if path.is_file()
    }
    report = tmp_path / "external_checks" / mode / "quick.json"
    outcome = verify.verify_results(directory, mode=mode, report_path=report)
    after = {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*") if path.is_file()
    }
    assert before == after
    assert json.loads(report.read_text("utf-8")) == outcome
    assert outcome["experiment_name"] == "quick"
    assert outcome["manifest_files_checked"] == 0


def test_cli_accepts_external_report_path():
    args = verify.build_parser().parse_args([
        "--results", "results/quick", "--report", "results/phase4_checks/quick.json"
    ])
    assert args.mode == "strict"
    assert args.report == "results/phase4_checks/quick.json"
