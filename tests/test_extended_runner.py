from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path

import pytest

from pde_image_denoising.experiments import (
    expected_row_count,
    expected_summary_count,
    load_config,
    run_and_write,
    write_latex_summary_from_csv,
)


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_extended_configuration_and_counts():
    config = load_config(ROOT / "configs" / "extended.json")
    assert config["experiment_name"] == "extended"
    assert config["output_dir"] == "results/extended"
    assert config["image_shape"] == [128, 128]
    assert config["images"] == ["geometric_shapes", "ramps_and_edges"]
    assert config["sigmas"] == [0.025, 0.05, 0.10]
    assert config["seeds"] == list(range(10))
    assert (config["dx"], config["dy"], config["dt"]) == (1.0, 1.0, 0.20)
    assert config["checkpoints"] == [0, 1, 2, 5, 10, 20, 40, 80]
    assert config["perona_malik"] == {
        "conductions": ["exponential", "rational"],
        "K_values": [0.025, 0.05, 0.10, 0.20],
    }
    assert config["representative"] == {
        "image": "geometric_shapes", "sigma": 0.10,
        "seed": 0, "K": 0.10, "checkpoint": 20,
    }
    assert config["data_range"] == 1.0
    assert expected_row_count(config) == 4380
    assert expected_summary_count(config) == 438


def test_probe_preserves_methods_grid_and_representative():
    full = load_config(ROOT / "configs" / "extended.json")
    probe = load_config(ROOT / "configs" / "extended_probe.json")
    for field in (
        "experiment_name", "image_shape", "dx", "dy", "dt", "checkpoints",
        "perona_malik", "representative", "data_range",
    ):
        assert probe[field] == full[field]
    assert probe["images"] == ["geometric_shapes"]
    assert probe["sigmas"] == [0.10]
    assert probe["seeds"] == [0]
    assert probe["output_dir"] == "results/extended_probe"
    assert expected_row_count(probe) == expected_summary_count(probe) == 73


@pytest.fixture
def small_extended():
    config = load_config(ROOT / "configs" / "extended_probe.json")
    config["image_shape"] = [8, 8]
    config["checkpoints"] = [0, 1, 2]
    config["representative"]["checkpoint"] = 2
    return config


def test_extended_runner_log_and_manifest_use_experiment_identity(
    tmp_path, monkeypatch, small_extended
):
    from pde_image_denoising import extended_analysis, plotting

    monkeypatch.setattr(plotting, "generate_quick_figures", lambda *args: [])
    monkeypatch.setattr(
        extended_analysis, "generate_extended_analysis",
        lambda *args: {"figure_paths": [], "table_paths": []},
    )
    destination = tmp_path / "extended"
    outcome = run_and_write(small_extended, destination)
    assert outcome["experiment_name"] == "extended"
    assert outcome["solver_trajectories"] == 9
    assert outcome["metrics_rows"] == 28
    assert (destination / "tables" / "representative_summary.tex").is_file()
    assert (destination / "run.log").read_text("utf-8").startswith("experiment=extended\n")
    manifest = json.loads((destination / "manifest.json").read_text("utf-8"))
    assert manifest["experiment_name"] == "extended"
    assert manifest["config_sha256"] == hashlib.sha256(
        (destination / "config_used.json").read_bytes()
    ).hexdigest()
    for entry in manifest["files"]:
        path = destination / entry["path"]
        assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert entry["size_bytes"] == path.stat().st_size


def test_extended_runner_refuses_existing_destination(tmp_path, small_extended):
    destination = tmp_path / "extended"
    destination.mkdir()
    marker = destination / "existing.txt"
    marker.write_text("preserve me\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        run_and_write(small_extended, destination)
    assert marker.read_text("utf-8") == "preserve me\n"


def test_quick_writer_preserves_legacy_names_and_does_not_add_manifest(
    tmp_path, monkeypatch, small_extended
):
    from pde_image_denoising import plotting

    config = copy.deepcopy(small_extended)
    config["experiment_name"] = "quick"
    monkeypatch.setattr(plotting, "generate_quick_figures", lambda *args: [])
    destination = tmp_path / "quick"
    outcome = run_and_write(config, destination)
    assert outcome["experiment_name"] == "quick"
    assert outcome["extended_analysis"] is None
    assert (destination / "tables" / "quick_summary.tex").is_file()
    assert (destination / "run.log").read_text("utf-8").startswith("experiment=quick\n")
    assert not (destination / "manifest.json").exists()


def test_representative_latex_does_not_round_K_0025_to_003(tmp_path, small_extended):
    summary_path = tmp_path / "summary.csv"
    row = {
        "image": "geometric_shapes", "sigma": "0.1", "method": "perona_malik",
        "conduction": "exponential", "K": "0.025", "n": "2",
        "mse_mean": "0.01", "psnr_mean": "20", "ssim_mean": "0.5",
    }
    with summary_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    target = tmp_path / "representative_summary.tex"
    assert write_latex_summary_from_csv(summary_path, target, small_extended) == 1
    assert "exponential / 0.025" in target.read_text("utf-8")
