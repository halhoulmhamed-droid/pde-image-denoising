"""Verify experiment artifacts, determinism, shared inputs, and heat accuracy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import numpy as np

from .experiments import (
    METRICS_FIELDS,
    SUMMARY_FIELDS,
    SUMMARY_GROUP_FIELDS,
    SUMMARY_VALUE_FIELDS,
    array_sha256,
    compute_experiment,
    expected_row_count,
    expected_summary_count,
    float_token,
    load_config,
    summarise_records,
)
from .heat import heat_diffusion

VERIFICATION_MODES = ("strict", "numerical")
NUMERICAL_RTOL = 1e-10
NUMERICAL_ATOL = 1e-12
METRIC_VALUE_FIELDS = ["mse", "relative_l2", "psnr", "ssim"]


def discrete_neumann_mode_validation() -> dict[str, float | int]:
    height, width = 17, 19
    p, q = 2, 3
    dy, dx, dt, n_steps = 1.1, 0.8, 0.2, 7
    rows = np.arange(height, dtype=np.float64)
    columns = np.arange(width, dtype=np.float64)
    mode = np.cos(np.pi * p * (rows + 0.5) / height)[:, None] * np.cos(
        np.pi * q * (columns + 0.5) / width
    )[None, :]
    eigenvalue = (
        -4.0 * np.sin(np.pi * p / (2.0 * height)) ** 2 / dy**2
        - 4.0 * np.sin(np.pi * q / (2.0 * width)) ** 2 / dx**2
    )
    expected = (1.0 + dt * eigenvalue) ** n_steps * mode
    numerical = heat_diffusion(
        mode, n_steps, dt=dt, dx=dx, dy=dy
    )
    return {
        "height": height,
        "width": width,
        "p": p,
        "q": q,
        "n_steps": n_steps,
        "eigenvalue": float(eigenvalue),
        "max_abs_error": float(np.max(np.abs(numerical - expected))),
    }


def refinement_validation() -> dict[str, Any]:
    p, q, final_time = 1, 1, 0.01
    spatial_errors: dict[str, float] = {}
    continuous_eigenvalue = -(np.pi * p) ** 2 - (np.pi * q) ** 2
    for size in (16, 32):
        dx = dy = 1.0 / size
        discrete_eigenvalue = (
            -4.0 * np.sin(np.pi * p / (2.0 * size)) ** 2 / dy**2
            - 4.0 * np.sin(np.pi * q / (2.0 * size)) ** 2 / dx**2
        )
        spatial_errors[str(size)] = abs(
            math.exp(discrete_eigenvalue * final_time)
            - math.exp(continuous_eigenvalue * final_time)
        )

    height, width = 16, 20
    dy, dx = 1.0 / height, 1.0 / width
    p, q, final_time = 1, 2, 0.001
    discrete_eigenvalue = (
        -4.0 * np.sin(np.pi * p / (2.0 * height)) ** 2 / dy**2
        - 4.0 * np.sin(np.pi * q / (2.0 * width)) ** 2 / dx**2
    )
    exact_amplitude = math.exp(discrete_eigenvalue * final_time)
    temporal_errors: dict[str, float] = {}
    for steps in (8, 16):
        dt = final_time / steps
        numerical_amplitude = (1.0 + dt * discrete_eigenvalue) ** steps
        temporal_errors[str(steps)] = abs(numerical_amplitude - exact_amplitude)

    return {
        "spatial_semidiscrete_vs_continuous_amplitude_errors": spatial_errors,
        "temporal_euler_vs_semidiscrete_amplitude_errors": temporal_errors,
        "spatial_error_decreases": bool(
            spatial_errors["32"] < spatial_errors["16"]
        ),
        "temporal_error_decreases": bool(
            temporal_errors["16"] < temporal_errors["8"]
        ),
        "claim": (
            "Separate amplitude checks only: spatial comparison uses the exact "
            "semi-discrete exponential, temporal comparison fixes the grid. "
            "No convergence order is inferred from two levels."
        ),
    }


def _read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != fields:
            raise AssertionError(f"{path.name} columns are not the documented schema")
        rows = list(reader)
    if not rows:
        raise AssertionError(f"{path.name} contains no data rows")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise AssertionError(f"{path.name} contains a malformed row")
    return rows


def _numeric_equal(left: float, right: float, *, mode: str) -> bool:
    if math.isnan(left) or math.isnan(right):
        return False
    if left == right:
        return True
    if mode == "strict" or not (math.isfinite(left) and math.isfinite(right)):
        return False
    return abs(left - right) <= NUMERICAL_ATOL + NUMERICAL_RTOL * abs(right)


def _typed_group_values(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise CSV keys before grouping; never compare lexicographic numbers."""
    values = {field: row[field] for field in SUMMARY_GROUP_FIELDS}
    values["n"] = int(row["n"])
    for field in ("sigma", "dx", "dy", "dt", "diffusion_time"):
        values[field] = float(row[field])
        if not math.isfinite(values[field]):
            raise AssertionError(f"non-finite grouping key: {field}")
    values["K"] = "" if row["K"] == "" else float(row["K"])
    if values["K"] != "" and not math.isfinite(values["K"]):
        raise AssertionError("non-finite grouping key: K")
    return values


def _group_key(row: dict[str, Any]) -> tuple[Any, ...]:
    values = _typed_group_values(row)
    return tuple(values[field] for field in SUMMARY_GROUP_FIELDS)


def _verify_summary(
    existing: list[dict[str, str]],
    metrics: list[dict[str, str]],
    config: dict[str, Any],
    *,
    mode: str,
) -> int:
    """Recompute all aggregates from the stored CSV, including recorded timings."""
    typed_metrics: list[dict[str, Any]] = []
    seeds_by_group: dict[tuple[Any, ...], list[int]] = {}
    for index, row in enumerate(metrics):
        typed = _typed_group_values(row)
        typed["seed"] = int(row["seed"])
        for field in SUMMARY_VALUE_FIELDS:
            typed[field] = float(row[field])
            if math.isnan(typed[field]):
                raise AssertionError(f"metrics row {index}: NaN in {field}")
        duration = typed["duration_seconds"]
        if not math.isfinite(duration) or duration < 0.0:
            raise AssertionError(f"metrics row {index}: invalid duration_seconds")
        typed_metrics.append(typed)
        seeds_by_group.setdefault(_group_key(typed), []).append(typed["seed"])

    configured_seeds = set(config["seeds"])
    for key, seeds in seeds_by_group.items():
        if len(seeds) != len(set(seeds)) or set(seeds) != configured_seeds:
            raise AssertionError(f"metrics group {key}: invalid or duplicate seeds")

    expected = {_group_key(row): row for row in summarise_records(typed_metrics)}
    actual: dict[tuple[Any, ...], dict[str, str]] = {}
    for row in existing:
        key = _group_key(row)
        if key in actual:
            raise AssertionError(f"summary.csv contains a duplicate grouping key: {key}")
        actual[key] = row
    if set(actual) != set(expected):
        raise AssertionError("summary.csv grouping keys differ from metrics.csv")

    for key, current in expected.items():
        stored = actual[key]
        if int(stored["n_seeds"]) != current["n_seeds"]:
            raise AssertionError(f"summary group {key}: mismatch in n_seeds")
        for field in SUMMARY_VALUE_FIELDS:
            for statistic in ("mean", "std"):
                column = f"{field}_{statistic}"
                if not _numeric_equal(
                    float(stored[column]), float(current[column]), mode=mode
                ):
                    raise AssertionError(f"summary group {key}: mismatch in {column}")
    return len(expected)


def _compare_records(
    existing: list[dict[str, str]],
    recomputed: list[dict[str, Any]],
    *,
    mode: str,
) -> list[dict[str, Any]]:
    if len(existing) != len(recomputed):
        raise AssertionError(
            f"metrics row count differs: {len(existing)} != {len(recomputed)}"
        )
    text_fields = [
        "image",
        "method",
        "conduction",
        "true_sha256",
        "noisy_sha256",
    ]
    integer_fields = ["seed", "n"]
    numeric_fields = [
        "sigma",
        "dx",
        "dy",
        "dt",
        "diffusion_time",
    ]
    hash_differences: list[dict[str, Any]] = []
    for index, (stored, current) in enumerate(
        zip(existing, recomputed, strict=True)
    ):
        for field in text_fields:
            if stored[field] != str(current[field]):
                raise AssertionError(f"row {index}: mismatch in {field}")
        for field in integer_fields:
            if int(stored[field]) != int(current[field]):
                raise AssertionError(f"row {index}: mismatch in {field}")
        if (stored["K"] == "") != (current["K"] == ""):
            raise AssertionError(f"row {index}: mismatch in K presence")
        if stored["K"] and float(stored["K"]) != float(current["K"]):
            raise AssertionError(f"row {index}: mismatch in K")
        for field in numeric_fields:
            left, right = float(stored[field]), float(current[field])
            if left != right:
                raise AssertionError(f"row {index}: mismatch in {field}")
        for field in METRIC_VALUE_FIELDS:
            if not _numeric_equal(
                float(stored[field]), float(current[field]), mode=mode
            ):
                raise AssertionError(f"row {index}: mismatch in {field}")
        for field in ("true_sha256", "noisy_sha256", "output_sha256"):
            if re.fullmatch(r"[0-9a-f]{64}", stored[field]) is None:
                raise AssertionError(f"row {index}: invalid {field}")
        if stored["output_sha256"] != current["output_sha256"]:
            if mode == "strict":
                raise AssertionError(f"row {index}: mismatch in output_sha256")
            hash_differences.append(
                {
                    "row_index": index,
                    **_typed_group_values(stored),
                    "seed": int(stored["seed"]),
                    "stored_output_sha256": stored["output_sha256"],
                    "recomputed_output_sha256": current["output_sha256"],
                }
            )
    return hash_differences


def _compare_npz(
    path: Path, recomputed: dict[str, np.ndarray], *, mode: str
) -> tuple[dict[str, np.ndarray], list[dict[str, str]]]:
    stored_arrays = {}
    hash_differences = []
    with np.load(path, allow_pickle=False) as archive:
        if len(archive.files) != len(set(archive.files)) or set(archive.files) != set(recomputed):
            raise AssertionError(f"array keys differ in {path}")
        for key in archive.files:
            stored, current = archive[key], recomputed[key]
            if stored.shape != current.shape or stored.dtype != current.dtype:
                raise AssertionError(f"array shape or dtype differs for {key} in {path}")
            if stored.dtype != np.dtype(np.float64) or not np.all(np.isfinite(stored)):
                raise AssertionError(f"invalid archived array for {key} in {path}")
            equal = (
                np.array_equal(stored, current)
                if mode == "strict"
                else np.allclose(
                    stored, current, rtol=NUMERICAL_RTOL, atol=NUMERICAL_ATOL,
                    equal_nan=False,
                )
            )
            if not equal:
                raise AssertionError(f"array mismatch for {key} in {path}")
            stored_hash, current_hash = array_sha256(stored), array_sha256(current)
            if stored_hash != current_hash:
                if mode == "strict":
                    raise AssertionError(f"array hash mismatch for {key} in {path}")
                hash_differences.append(
                    {
                        "array": key,
                        "stored_sha256": stored_hash,
                        "recomputed_sha256": current_hash,
                    }
                )
            stored_arrays[key] = stored
    return stored_arrays, hash_differences


def _verify_archived_hashes(
    records: list[dict[str, str]],
    inputs: dict[str, np.ndarray],
    representative_arrays: dict[str, np.ndarray],
    config: dict[str, Any],
) -> int:
    """Archived data must match recorded hashes exactly, in both modes."""
    input_hashes = {key: array_sha256(value) for key, value in inputs.items()}
    representative_hashes = {
        key: array_sha256(value) for key, value in representative_arrays.items()
    }
    representative = config["representative"]
    checked_outputs = 0
    for index, row in enumerate(records):
        truth_key = f"truth__{row['image']}"
        noisy_key = (
            f"noisy__{row['image']}__sigma_{float_token(float(row['sigma']))}"
            f"__seed_{int(row['seed'])}"
        )
        if row["true_sha256"] != input_hashes[truth_key]:
            raise AssertionError(f"row {index}: archived true hash mismatch")
        if row["noisy_sha256"] != input_hashes[noisy_key]:
            raise AssertionError(f"row {index}: archived noisy hash mismatch")
        output_hash = None
        if int(row["n"]) == 0:
            output_hash = input_hashes[noisy_key]
        if (
            row["image"] == representative["image"]
            and float(row["sigma"]) == float(representative["sigma"])
            and int(row["seed"]) == int(representative["seed"])
        ):
            checkpoint = int(row["n"])
            if row["method"] == "noisy":
                output_key = "noisy"
            elif row["method"] == "heat":
                output_key = f"heat_n{checkpoint}"
            else:
                output_key = (
                    f"pm_{row['conduction']}_K{float_token(float(row['K']))}"
                    f"_n{checkpoint}"
                )
            representative_output_hash = representative_hashes[output_key]
            if (
                output_hash is not None
                and representative_output_hash != output_hash
            ):
                raise AssertionError(f"row {index}: archived initial output differs")
            output_hash = representative_output_hash
        if output_hash is not None:
            if row["output_sha256"] != output_hash:
                raise AssertionError(f"row {index}: archived output hash mismatch")
            checked_outputs += 1
    for name in ("truth", "noisy"):
        input_key = (
            f"truth__{representative['image']}"
            if name == "truth"
            else (
                f"noisy__{representative['image']}"
                f"__sigma_{float_token(representative['sigma'])}"
                f"__seed_{representative['seed']}"
            )
        )
        if representative_hashes[name] != input_hashes[input_key]:
            raise AssertionError(f"representative {name} differs from archived input")
    return checked_outputs


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_manifest(directory: Path, config: dict[str, Any]) -> int:
    """Check immutable generated artifacts exactly, in either comparison mode."""
    manifest = json.loads((directory / "manifest.json").read_text("utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {
        "experiment_name", "config_sha256", "files"
    }:
        raise AssertionError("manifest.json has an invalid schema")
    if manifest["experiment_name"] != config["experiment_name"]:
        raise AssertionError("manifest experiment_name differs from config_used.json")
    config_digest = _file_sha256(directory / "config_used.json")
    if manifest["config_sha256"] != config_digest:
        raise AssertionError("manifest config_sha256 differs from config_used.json")
    entries = manifest["files"]
    if not isinstance(entries, list) or not entries:
        raise AssertionError("manifest files must be a non-empty list")
    omitted = {"manifest.json", "verification.json", "verification_numerical.json"}
    listed: set[str] = set()
    root = directory.resolve()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "path", "sha256", "size_bytes"
        }:
            raise AssertionError("manifest file entry has an invalid schema")
        relative = entry["path"]
        if not isinstance(relative, str) or not relative:
            raise AssertionError("manifest path must be a non-empty relative path")
        posix_path = PurePosixPath(relative)
        windows_path = PureWindowsPath(relative)
        if (
            "\\" in relative
            or posix_path.is_absolute()
            or windows_path.drive
            or windows_path.root
            or ".." in posix_path.parts
            or ":" in relative
            or posix_path.as_posix() != relative
            or relative in omitted
        ):
            raise AssertionError(f"unsafe or reserved manifest path: {relative}")
        if relative in listed:
            raise AssertionError(f"duplicate manifest path: {relative}")
        listed.add(relative)
        path = directory.joinpath(*posix_path.parts)
        if not path.resolve().is_relative_to(root):
            raise AssertionError(f"manifest path escapes results directory: {relative}")
        if not path.is_file():
            raise AssertionError(f"missing manifest artifact: {relative}")
        digest = entry["sha256"]
        size = entry["size_bytes"]
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise AssertionError(f"invalid manifest sha256: {relative}")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise AssertionError(f"invalid manifest size_bytes: {relative}")
        if path.stat().st_size != size or _file_sha256(path) != digest:
            raise AssertionError(f"manifest integrity mismatch: {relative}")
    existing = {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file() and path.relative_to(directory).as_posix() not in omitted
    }
    if listed != existing:
        raise AssertionError(
            "manifest inventory differs from result files: "
            f"missing={sorted(existing - listed)}, extra={sorted(listed - existing)}"
        )
    return len(listed)


def verify_results(
    results: str | Path, *, mode: str = "strict", report_path: str | Path | None = None
) -> dict[str, Any]:
    if mode not in VERIFICATION_MODES:
        raise ValueError(f"verification mode must be one of {VERIFICATION_MODES}")
    directory = Path(results)
    config = load_config(directory / "config_used.json")
    experiment_name = config["experiment_name"]
    required = [
        directory / "metrics.csv",
        directory / "summary.csv",
        directory / "config_used.json",
        directory / "environment.json",
        directory / "run.log",
        directory / "arrays" / "inputs.npz",
        directory / "arrays" / "representative_outputs.npz",
        directory / "tables" / (
            "quick_summary.tex" if experiment_name == "quick" else "representative_summary.tex"
        ),
    ]
    figure_stems = [
        "comparison",
        "metric_curves",
        "k_comparison",
        "intensity_profile",
        "gradient_maps",
    ]
    required.extend(
        directory / "figures" / f"{stem}.{extension}"
        for stem in figure_stems
        for extension in ("png", "pdf")
    )
    if experiment_name == "extended":
        required.extend(
            directory / relative
            for relative in (
                "manifest.json", "analysis.json",
                "tables/extended_common_checkpoints.csv",
                "tables/extended_common_checkpoints.tex",
                "tables/oracle_exploratory.csv", "tables/oracle_exploratory.tex",
            )
        )
        required.extend(
            directory / "figures" / (
                f"{kind}_{image}_sigma{float_token(float(sigma))}.{extension}"
            )
            for image in config["images"]
            for sigma in config["sigmas"]
            for kind in ("metric_curves", "k_sensitivity")
            for extension in ("png", "pdf")
        )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing {experiment_name} artifacts: {missing}")

    manifest_count = 0
    if experiment_name == "extended":
        manifest_count = _verify_manifest(directory, config)
        log_lines = (directory / "run.log").read_text("utf-8").splitlines()
        if f"experiment={experiment_name}" not in log_lines:
            raise AssertionError("run.log does not identify the configured experiment")
    stored_metrics = _read_csv(directory / "metrics.csv", METRICS_FIELDS)
    stored_summary = _read_csv(directory / "summary.csv", SUMMARY_FIELDS)
    if len(stored_metrics) != expected_row_count(config):
        raise AssertionError("unexpected metrics.csv row count")
    if len(stored_summary) != expected_summary_count(config):
        raise AssertionError("unexpected summary.csv row count")

    summary_groups = _verify_summary(
        stored_summary, stored_metrics, config, mode=mode
    )
    recomputed = compute_experiment(config, measure_time=False)
    output_hash_differences = _compare_records(
        stored_metrics, recomputed.records, mode=mode
    )
    input_arrays, _ = _compare_npz(
        directory / "arrays" / "inputs.npz", recomputed.input_arrays, mode="strict"
    )
    representative_arrays, array_hash_differences = _compare_npz(
        directory / "arrays" / "representative_outputs.npz",
        recomputed.representative_arrays,
        mode=mode,
    )
    archived_output_hash_count = _verify_archived_hashes(
        stored_metrics, input_arrays, representative_arrays, config
    )

    noisy_hashes: dict[tuple[str, str, str], set[str]] = {}
    for row in stored_metrics:
        key = (row["image"], row["sigma"], row["seed"])
        noisy_hashes.setdefault(key, set()).add(row["noisy_sha256"])
    if any(len(hashes) != 1 for hashes in noisy_hashes.values()):
        raise AssertionError("a noisy observation differs between methods")

    heat_mode = discrete_neumann_mode_validation()
    refinement = refinement_validation()
    if float(heat_mode["max_abs_error"]) > 5e-13:
        raise AssertionError("independent heat eigenmode validation failed")
    if not refinement["spatial_error_decreases"]:
        raise AssertionError("spatial refinement check failed")
    if not refinement["temporal_error_decreases"]:
        raise AssertionError("temporal refinement check failed")

    payload = {
        "status": "passed",
        "experiment_name": experiment_name,
        "manifest_files_checked": manifest_count,
        "manifest_integrity_exact": experiment_name == "extended",
        "verification_mode": mode,
        "tolerances": {
            "rtol": 0.0 if mode == "strict" else NUMERICAL_RTOL,
            "atol": 0.0 if mode == "strict" else NUMERICAL_ATOL,
        },
        "exact_reproduction": mode == "strict",
        "reproduction_claim": (
            "exact" if mode == "strict" else "within_numerical_tolerances"
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "metrics_rows": len(stored_metrics),
        "summary_rows": len(stored_summary),
        "summary_groups_checked": summary_groups,
        "summary_statistics_checked": summary_groups * 2 * len(SUMMARY_VALUE_FIELDS),
        "summary_aggregation_source": "recorded metrics.csv values",
        "duration_statistics_checked_from_recorded_values": True,
        "deterministic_columns_recomputed": True,
        "duration_columns_compared": False,
        "shared_noisy_observations": len(noisy_hashes),
        "input_arrays_compared": len(input_arrays),
        "representative_arrays_compared": len(representative_arrays),
        "archived_array_integrity_exact": True,
        "archived_output_hashes_checked": archived_output_hash_count,
        "unarchived_outputs_integrity_note": (
            "Only checkpoint-zero and representative outputs have archived arrays. "
            "Other output hashes are compared to recalculation only."
        ),
        "recomputed_output_hash_differences": output_hash_differences,
        "recomputed_array_hash_differences": array_hash_differences,
        "required_artifacts_present": len(required),
        "heat_discrete_neumann_mode": heat_mode,
        "refinement_checks": refinement,
    }
    report_name = "verification.json" if mode == "strict" else "verification_numerical.json"
    destination = directory / report_name if report_path is None else Path(report_path)
    if report_path is not None:
        destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, help="Experiment-results directory")
    parser.add_argument(
        "--mode", choices=VERIFICATION_MODES, default="strict",
        help="strict (exact, default) or numerical (explicit tolerance-based check)",
    )
    parser.add_argument(
        "--report", default=None,
        help="Optional report path; leaves the default results report unchanged",
    )
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    outcome = verify_results(
        arguments.results, mode=arguments.mode, report_path=arguments.report
    )
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    main()
