"""Analysis tests use hand-declared CSV fixtures; no scientific run is made."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

from pde_image_denoising.experiments import METRICS_FIELDS, SUMMARY_FIELDS
from pde_image_denoising.extended_analysis import (
    common_checkpoint_rows,
    generate_extended_analysis,
    grouped_metric_curves,
    oracle_and_rankings,
    read_analysis_csv,
    select_case_rows,
    sensitivity_checkpoints,
    write_common_checkpoint_latex,
)


def _summary_row(method, conduction, K, n, psnr, ssim):
    mse = 10.0 ** (-psnr / 10.0)
    return {
        "image": "geometric_shapes", "sigma": "0.1", "method": method,
        "conduction": conduction, "K": K, "dx": "1.0", "dy": "1.0",
        "dt": "0.2", "n": str(n), "diffusion_time": str(n * 0.2),
        "n_seeds": "2", "mse_mean": str(mse), "mse_std": str(mse / 10),
        "relative_l2_mean": str(math.sqrt(mse)), "relative_l2_std": "0.01",
        "psnr_mean": str(psnr), "psnr_std": "0.5", "ssim_mean": str(ssim),
        "ssim_std": "0.025", "duration_seconds_mean": str(n * 0.01),
        "duration_seconds_std": str(n * 0.001),
    }


@pytest.fixture
def csv_fixture(tmp_path):
    config = {
        "experiment_name": "extended", "images": ["geometric_shapes"],
        "sigmas": [0.1], "seeds": [0, 1], "dt": 0.2,
        "checkpoints": [0, 1, 2],
        "perona_malik": {"conductions": ["exponential", "rational"],
                         "K_values": [0.05, 0.1]},
    }
    summary = [_summary_row("noisy", "", "", 0, 20.0, 0.2)]
    variants = [
        ("heat", "", "", (25.0, 24.0), (0.8, 0.9)),
        ("perona_malik", "exponential", "0.05", (30.0, 27.0), (0.5, 0.6)),
        ("perona_malik", "exponential", "0.1", (29.0, 28.0), (0.7, 0.8)),
        ("perona_malik", "rational", "0.05", (27.0, 26.0), (0.6, 0.85)),
        ("perona_malik", "rational", "0.1", (28.0, 29.0), (0.7, 0.82)),
    ]
    for method, conduction, K, psnr_values, ssim_values in variants:
        summary.append(_summary_row(method, conduction, K, 0, 20.0, 0.2))
        for n in (1, 2):
            summary.append(_summary_row(method, conduction, K, n,
                                        psnr_values[n - 1], ssim_values[n - 1]))
    records = []
    for row in summary:
        for seed in config["seeds"]:
            records.append({
                **{field: row[field] for field in METRICS_FIELDS if field in row},
                "seed": seed,
                **{field: row[f"{field}_mean"] for field in
                   ("mse", "relative_l2", "psnr", "ssim", "duration_seconds")},
                "true_sha256": "a" * 64, "noisy_sha256": str(seed) * 64,
                "output_sha256": "b" * 64,
            })
    for filename, rows, fields in (
        ("metrics.csv", records, METRICS_FIELDS),
        ("summary.csv", summary, SUMMARY_FIELDS),
    ):
        with (tmp_path / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    return tmp_path, config, summary


def test_curves_use_recorded_mean_sample_std_and_diffusion_time(csv_fixture):
    _, config, summary = csv_fixture
    shuffled = list(reversed(select_case_rows(summary, "geometric_shapes", 0.1)))
    curves = grouped_metric_curves(shuffled, "psnr")
    assert len(curves) == 5
    assert ("noisy", "", "") not in curves
    assert curves[("heat", "", "")] == {
        "time": [0.0, 0.2, 0.4], "mean": [20.0, 25.0, 24.0],
        "std": [0.5, 0.5, 0.5],
    }
    assert sensitivity_checkpoints(config) == [2]


def test_sensitivity_checkpoints_are_fixed_intersections():
    assert sensitivity_checkpoints({"checkpoints": [0, 1, 2, 5, 10, 20, 40, 80]}) == [5, 20, 80]
    assert sensitivity_checkpoints({"checkpoints": [0, 5, 10]}) == [5]
    with pytest.raises(ValueError, match="positive checkpoint"):
        sensitivity_checkpoints({"checkpoints": [0]})


def test_common_tables_publish_all_variants_at_every_positive_checkpoint(csv_fixture):
    _, config, summary = csv_fixture
    rows = common_checkpoint_rows(summary, config)
    assert len(rows) == 12
    assert {row["comparison_n"] for row in rows} == {"1", "2"}
    for checkpoint in ("1", "2"):
        selected = [row for row in rows if row["comparison_n"] == checkpoint]
        assert len(selected) == 6
        assert sum(row["method"] == "noisy" for row in selected) == 1
        assert sum(row["method"] == "perona_malik" for row in selected) == 4
        assert all(row["n"] == checkpoint for row in selected if row["method"] != "noisy")


def test_oracle_selection_is_explicit_and_rank_disagreements_are_counted(csv_fixture):
    _, config, summary = csv_fixture
    winners, report = oracle_and_rankings(summary, config)
    assert len(winners) == 2
    assert winners[0]["oracle_criterion"] == "psnr"
    assert winners[0]["conduction"] == "exponential"
    assert winners[0]["K"] == "0.05"
    assert winners[0]["n"] == "1"
    assert winners[1]["oracle_criterion"] == "ssim"
    assert winners[1]["method"] == "heat"
    assert winners[1]["n"] == "2"
    assert report["selection_label"] == "oracle exploratoire"
    assert report["oracle_psnr_ssim_configuration_disagreements"] == 1
    assert report["fixed_checkpoint_comparison_count"] == 2
    assert report["fixed_checkpoint_top_disagreements"] == 2
    assert report["fixed_checkpoint_discordant_pairs"] > 0


def test_analysis_reads_csv_and_produces_all_announced_artifacts(csv_fixture):
    directory, config, _ = csv_fixture
    result = generate_extended_analysis(directory, config)
    assert result["source_metrics_rows"] == 32
    assert result["source_summary_rows"] == 16
    assert result["common_checkpoint_rows"] == 12
    assert result["oracle_rows"] == 2
    assert result["sensitivity_checkpoints"] == [2]
    assert len(result["figure_paths"]) == 4
    assert len(result["table_paths"]) == 4
    for path in result["figure_paths"] + result["table_paths"]:
        assert Path(path).is_file()
        assert Path(path).stat().st_size > 0
    stored = json.loads((directory / "analysis.json").read_text("utf-8"))
    assert stored["source_summary_csv"] == "summary.csv"
    assert "ddof=1" in stored["dispersion"]
    assert "oracle exploratoire" in (directory / "tables/oracle_exploratory.tex").read_text("utf-8")


def test_latex_is_generated_from_csv_values_not_memory(csv_fixture):
    directory, config, _ = csv_fixture
    generate_extended_analysis(directory, config)
    csv_path = directory / "tables/extended_common_checkpoints.csv"
    rows = read_analysis_csv(csv_path, ["comparison_n", *SUMMARY_FIELDS])
    rows[0]["psnr_mean"] = "123.456"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["comparison_n", *SUMMARY_FIELDS])
        writer.writeheader()
        writer.writerows(rows)
    target = directory / "tables/regenerated.tex"
    assert write_common_checkpoint_latex(csv_path, target) == 12
    assert "123.46" in target.read_text("utf-8")


def test_analysis_rejects_incorrect_csv_schema(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("image,psnr_mean\nexample,10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        read_analysis_csv(path, SUMMARY_FIELDS)


def test_curve_duplicate_checkpoint_is_rejected(csv_fixture):
    _, _, summary = csv_fixture
    heat = [row for row in summary if row["method"] == "heat"]
    with pytest.raises(ValueError, match="duplicate checkpoint"):
        grouped_metric_curves(heat + [heat[0]], "ssim")
