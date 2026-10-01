"""Quick and extended experiment orchestration with traceable outputs."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib
import numpy as np

from .boundaries import FloatArray, validate_scheme_parameters
from .datasets import DATASET_NAMES, get_dataset
from .heat import heat_trajectory
from .metrics import compute_metrics
from .noise import add_gaussian_noise
from .perona_malik import CONDUCTION_NAMES, perona_malik_trajectory

METRICS_FIELDS = [
    "image",
    "sigma",
    "seed",
    "method",
    "conduction",
    "K",
    "dx",
    "dy",
    "dt",
    "n",
    "diffusion_time",
    "mse",
    "relative_l2",
    "psnr",
    "ssim",
    "duration_seconds",
    "true_sha256",
    "noisy_sha256",
    "output_sha256",
]

SUMMARY_GROUP_FIELDS = [
    "image",
    "sigma",
    "method",
    "conduction",
    "K",
    "dx",
    "dy",
    "dt",
    "n",
    "diffusion_time",
]

SUMMARY_VALUE_FIELDS = ["mse", "relative_l2", "psnr", "ssim", "duration_seconds"]

SUMMARY_FIELDS = (
    SUMMARY_GROUP_FIELDS
    + ["n_seeds"]
    + [
        item
        for field in SUMMARY_VALUE_FIELDS
        for item in (f"{field}_mean", f"{field}_std")
    ]
)


@dataclass
class ExperimentData:
    records: list[dict[str, Any]]
    input_arrays: dict[str, FloatArray]
    representative_arrays: dict[str, FloatArray]


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    required = {
        "experiment_name",
        "output_dir",
        "image_shape",
        "images",
        "sigmas",
        "seeds",
        "dx",
        "dy",
        "dt",
        "checkpoints",
        "perona_malik",
        "representative",
        "data_range",
    }
    missing = sorted(required.difference(config))
    if missing:
        raise ValueError(f"configuration is missing keys: {missing}")
    if config["experiment_name"] not in ("quick", "extended"):
        raise ValueError("experiment_name must be quick or extended")
    shape = config["image_shape"]
    if (
        not isinstance(shape, list)
        or len(shape) != 2
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 8
            for value in shape
        )
    ):
        raise ValueError("image_shape must contain two integers >= 8")
    images = config["images"]
    if not images or len(set(images)) != len(images):
        raise ValueError("images must be a non-empty list without duplicates")
    if any(name not in DATASET_NAMES for name in images):
        raise ValueError(f"images must be selected from {DATASET_NAMES}")
    sigmas = config["sigmas"]
    if not sigmas or any(
        not np.isscalar(value) or not np.isfinite(value) or value <= 0
        for value in sigmas
    ):
        raise ValueError("sigmas must be positive finite values")
    if len(set(sigmas)) != len(sigmas):
        raise ValueError("sigmas must not contain duplicates")
    seeds = config["seeds"]
    if not seeds or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in seeds
    ):
        raise ValueError("seeds must be non-negative integers")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must not contain duplicates")
    checkpoints = config["checkpoints"]
    if (
        not checkpoints
        or checkpoints != sorted(set(checkpoints))
        or checkpoints[0] != 0
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in checkpoints
        )
    ):
        raise ValueError("checkpoints must be sorted unique integers starting at 0")
    validate_scheme_parameters(
        n_steps=checkpoints[-1],
        dt=config["dt"],
        dx=config["dx"],
        dy=config["dy"],
    )
    pm = config["perona_malik"]
    if set(pm) != {"conductions", "K_values"}:
        raise ValueError("perona_malik must define conductions and K_values")
    if (
        not pm["conductions"]
        or any(value not in CONDUCTION_NAMES for value in pm["conductions"])
        or len(set(pm["conductions"])) != len(pm["conductions"])
    ):
        raise ValueError(f"invalid conduction list; supported: {CONDUCTION_NAMES}")
    if not pm["K_values"] or any(
        not np.isscalar(value) or not np.isfinite(value) or value <= 0
        for value in pm["K_values"]
    ):
        raise ValueError("K_values must be positive finite values")
    if len(set(pm["K_values"])) != len(pm["K_values"]):
        raise ValueError("K_values must not contain duplicates")
    if float(config["data_range"]) != 1.0:
        raise ValueError("the approved protocol requires data_range = 1.0")
    representative = config["representative"]
    if representative["image"] not in images:
        raise ValueError("representative image is not in the image list")
    if representative["sigma"] not in sigmas:
        raise ValueError("representative sigma is not in the sigma list")
    if representative["seed"] not in seeds:
        raise ValueError("representative seed is not in the seed list")
    if representative["checkpoint"] not in checkpoints:
        raise ValueError("representative checkpoint is not configured")
    if representative["K"] not in pm["K_values"]:
        raise ValueError("representative K is not configured")


def float_token(value: float) -> str:
    return format(float(value), ".12g").replace("-", "m").replace(".", "p")


def array_sha256(array: FloatArray) -> str:
    canonical = np.ascontiguousarray(array, dtype="<f8")
    digest = hashlib.sha256()
    digest.update(json.dumps(canonical.shape).encode("ascii"))
    digest.update(str(canonical.dtype).encode("ascii"))
    digest.update(canonical.tobytes(order="C"))
    return digest.hexdigest()


def expected_row_count(config: dict[str, Any]) -> int:
    observations = (
        len(config["images"]) * len(config["sigmas"]) * len(config["seeds"])
    )
    checkpoints = len(config["checkpoints"])
    pm_variants = len(config["perona_malik"]["conductions"]) * len(
        config["perona_malik"]["K_values"]
    )
    return observations * (1 + checkpoints * (1 + pm_variants))


def expected_summary_count(config: dict[str, Any]) -> int:
    per_image_sigma = 1 + len(config["checkpoints"]) * (
        1
        + len(config["perona_malik"]["conductions"])
        * len(config["perona_malik"]["K_values"])
    )
    return len(config["images"]) * len(config["sigmas"]) * per_image_sigma


def _is_representative(
    config: dict[str, Any], *, image: str, sigma: float, seed: int
) -> bool:
    representative = config["representative"]
    return (
        image == representative["image"]
        and float(sigma) == float(representative["sigma"])
        and int(seed) == int(representative["seed"])
    )


def _record(
    *,
    image_name: str,
    sigma: float,
    seed: int,
    method: str,
    conduction: str,
    K: float | str,
    dx: float,
    dy: float,
    dt: float,
    checkpoint: int,
    duration: float,
    truth: FloatArray,
    noisy: FloatArray,
    output: FloatArray,
    data_range: float,
) -> dict[str, Any]:
    values = compute_metrics(truth, output, data_range=data_range)
    return {
        "image": image_name,
        "sigma": float(sigma),
        "seed": int(seed),
        "method": method,
        "conduction": conduction,
        "K": K,
        "dx": float(dx),
        "dy": float(dy),
        "dt": float(dt),
        "n": int(checkpoint),
        "diffusion_time": float(checkpoint) * float(dt),
        **values,
        "duration_seconds": float(duration),
        "true_sha256": array_sha256(truth),
        "noisy_sha256": array_sha256(noisy),
        "output_sha256": array_sha256(output),
    }


def compute_experiment(
    config: dict[str, Any], *, measure_time: bool = True
) -> ExperimentData:
    """Compute the configured arrays and records without writing or plotting."""
    validate_config(config)
    shape = tuple(config["image_shape"])
    checkpoints = list(config["checkpoints"])
    dx, dy, dt = float(config["dx"]), float(config["dy"]), float(config["dt"])
    data_range = float(config["data_range"])

    records: list[dict[str, Any]] = []
    input_arrays: dict[str, FloatArray] = {}
    representative_arrays: dict[str, FloatArray] = {}

    for image_name in config["images"]:
        truth = get_dataset(image_name, shape)
        input_arrays[f"truth__{image_name}"] = truth.copy()
        for sigma in config["sigmas"]:
            for seed in config["seeds"]:
                noisy = add_gaussian_noise(truth, sigma=float(sigma), seed=int(seed))
                observation_key = (
                    f"noisy__{image_name}__sigma_{float_token(sigma)}"
                    f"__seed_{int(seed)}"
                )
                input_arrays[observation_key] = noisy.copy()
                representative = _is_representative(
                    config, image=image_name, sigma=float(sigma), seed=int(seed)
                )
                if representative:
                    representative_arrays["truth"] = truth.copy()
                    representative_arrays["noisy"] = noisy.copy()

                records.append(
                    _record(
                        image_name=image_name,
                        sigma=float(sigma),
                        seed=int(seed),
                        method="noisy",
                        conduction="",
                        K="",
                        dx=dx,
                        dy=dy,
                        dt=dt,
                        checkpoint=0,
                        duration=0.0,
                        truth=truth,
                        noisy=noisy,
                        output=noisy,
                        data_range=data_range,
                    )
                )

                heat_states, heat_times = heat_trajectory(
                    noisy,
                    checkpoints=checkpoints,
                    dt=dt,
                    dx=dx,
                    dy=dy,
                    measure_time=measure_time,
                )
                for checkpoint in checkpoints:
                    output = heat_states[checkpoint]
                    records.append(
                        _record(
                            image_name=image_name,
                            sigma=float(sigma),
                            seed=int(seed),
                            method="heat",
                            conduction="",
                            K="",
                            dx=dx,
                            dy=dy,
                            dt=dt,
                            checkpoint=checkpoint,
                            duration=heat_times[checkpoint],
                            truth=truth,
                            noisy=noisy,
                            output=output,
                            data_range=data_range,
                        )
                    )
                    if representative:
                        representative_arrays[f"heat_n{checkpoint}"] = output.copy()

                for conduction in config["perona_malik"]["conductions"]:
                    for K in config["perona_malik"]["K_values"]:
                        pm_states, pm_times = perona_malik_trajectory(
                            noisy,
                            checkpoints=checkpoints,
                            dt=dt,
                            dx=dx,
                            dy=dy,
                            K=float(K),
                            conduction=conduction,
                            measure_time=measure_time,
                        )
                        for checkpoint in checkpoints:
                            output = pm_states[checkpoint]
                            records.append(
                                _record(
                                    image_name=image_name,
                                    sigma=float(sigma),
                                    seed=int(seed),
                                    method="perona_malik",
                                    conduction=conduction,
                                    K=float(K),
                                    dx=dx,
                                    dy=dy,
                                    dt=dt,
                                    checkpoint=checkpoint,
                                    duration=pm_times[checkpoint],
                                    truth=truth,
                                    noisy=noisy,
                                    output=output,
                                    data_range=data_range,
                                )
                            )
                            if representative:
                                key = (
                                    f"pm_{conduction}_K{float_token(K)}"
                                    f"_n{checkpoint}"
                                )
                                representative_arrays[key] = output.copy()

    if len(records) != expected_row_count(config):
        raise RuntimeError("internal row-count mismatch")
    if not representative_arrays:
        raise RuntimeError("representative arrays were not captured")
    return ExperimentData(records, input_arrays, representative_arrays)


def summarise_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for record in records:
        key = tuple(record[field] for field in SUMMARY_GROUP_FIELDS)
        groups.setdefault(key, []).append(record)

    summary: list[dict[str, Any]] = []
    for key in sorted(groups):
        rows = groups[key]
        output = dict(zip(SUMMARY_GROUP_FIELDS, key, strict=True))
        output["n_seeds"] = len(rows)
        for field in SUMMARY_VALUE_FIELDS:
            values = [float(row[field]) for row in rows]
            output[f"{field}_mean"] = statistics.fmean(values)
            output[f"{field}_std"] = (
                statistics.stdev(values) if len(values) > 1 else 0.0
            )
        summary.append(output)
    return summary


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_escape(value: str) -> str:
    return value.replace("_", r"\_").replace("%", r"\%")


def write_latex_summary_from_csv(
    summary_path: Path, output_path: Path, config: dict[str, Any]
) -> int:
    """Generate a compact representative table by reading summary.csv."""
    representative = config["representative"]
    selected: list[dict[str, str]] = []
    with summary_path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            same_case = (
                row["image"] == representative["image"]
                and float(row["sigma"]) == float(representative["sigma"])
            )
            relevant_time = row["method"] == "noisy" or int(row["n"]) == int(
                representative["checkpoint"]
            )
            if same_case and relevant_time:
                selected.append(row)

    lines = [
        r"% Generated automatically from summary.csv; do not edit by hand.",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Méthode & Conduction / $K$ & $n$ & MSE & PSNR & SSIM \\",
        r"\midrule",
    ]
    for row in selected:
        method = {
            "noisy": "Bruitée",
            "heat": "Chaleur",
            "perona_malik": "Perona--Malik",
        }[row["method"]]
        detail = "--"
        if row["method"] == "perona_malik":
            detail = f"{row['conduction']} / {float(row['K']):g}"
        lines.append(
            f"{_latex_escape(method)} & {_latex_escape(detail)} & {row['n']} & "
            f"{float(row['mse_mean']):.5g} & "
            f"{float(row['psnr_mean']):.4f} & "
            f"{float(row['ssim_mean']):.4f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return len(selected)


def environment_metadata() -> dict[str, Any]:
    def installed_or_absent(distribution: str) -> str:
        try:
            return importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            return "not installed"

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "implementation": platform.python_implementation(),
        "packages": {
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "pytest": installed_or_absent("pytest"),
            "pde-image-denoising": importlib.metadata.version(
                "pde-image-denoising"
            ),
        },
        "metric_implementation": {
            "psnr": "NumPy formula with explicit data_range=1.0",
            "ssim": (
                "NumPy mean local SSIM, uniform valid 7x7 windows, "
                "sample covariances, K1=0.01, K2=0.03"
            ),
        },
        "optional_packages_not_used": {
            "scikit-image": installed_or_absent("scikit-image"),
            "scipy": installed_or_absent("scipy"),
            "reason": (
                "skimage.metrics transitively loaded a SciPy DLL blocked by "
                "Windows Application Control; NumPy metrics are used instead"
            ),
        },
        "numeric_dtype": "float64",
        "compute_device": "CPU",
    }


def write_result_manifest(destination: Path, experiment_name: str) -> dict[str, Any]:
    """Hash generated files, excluding the manifest and verification reports."""
    files = []
    for path in sorted(destination.rglob("*")):
        if (
            not path.is_file()
            or path.relative_to(destination).as_posix() in {
                "manifest.json", "verification.json", "verification_numerical.json"
            }
        ):
            continue
        files.append(
            {
                "path": path.relative_to(destination).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
    payload = {
        "experiment_name": experiment_name,
        "config_sha256": hashlib.sha256(
            (destination / "config_used.json").read_bytes()
        ).hexdigest(),
        "files": files,
    }
    (destination / "manifest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return payload


def run_and_write(config: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Run an approved quick or extended experiment and write its artifacts."""
    validate_config(config)
    destination = Path(output_dir)
    if (
        config["experiment_name"] == "extended"
        and destination.exists()
        and any(destination.iterdir())
    ):
        raise FileExistsError(
            f"extended destination is not empty; refusing to overwrite {destination}"
        )
    figures_dir = destination / "figures"
    arrays_dir = destination / "arrays"
    tables_dir = destination / "tables"
    for directory in (destination, figures_dir, arrays_dir, tables_dir):
        directory.mkdir(parents=True, exist_ok=True)

    total_start = perf_counter()
    data = compute_experiment(config, measure_time=True)
    summary = summarise_records(data.records)
    if len(summary) != expected_summary_count(config):
        raise RuntimeError("internal summary-count mismatch")

    _write_csv(destination / "metrics.csv", data.records, METRICS_FIELDS)
    _write_csv(destination / "summary.csv", summary, SUMMARY_FIELDS)
    (destination / "config_used.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (destination / "environment.json").write_text(
        json.dumps(environment_metadata(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    np.savez_compressed(arrays_dir / "inputs.npz", **data.input_arrays)
    np.savez_compressed(
        arrays_dir / "representative_outputs.npz", **data.representative_arrays
    )
    table_name = (
        "quick_summary.tex"
        if config["experiment_name"] == "quick"
        else "representative_summary.tex"
    )
    latex_rows = write_latex_summary_from_csv(
        destination / "summary.csv",
        tables_dir / table_name,
        config,
    )

    from .plotting import generate_quick_figures

    figure_paths = generate_quick_figures(
        figures_dir, config, data.records, data.representative_arrays
    )
    extended_analysis = None
    if config["experiment_name"] == "extended":
        from .extended_analysis import generate_extended_analysis

        extended_analysis = generate_extended_analysis(destination, config)
        figure_paths.extend(Path(path) for path in extended_analysis["figure_paths"])
    elapsed = perf_counter() - total_start
    terminal_checkpoint = max(config["checkpoints"])
    terminal_durations = [
        float(row["duration_seconds"])
        for row in data.records
        if row["method"] != "noisy" and int(row["n"]) == terminal_checkpoint
    ]
    log_lines = [
        f"experiment={config['experiment_name']}",
        f"started_and_completed_utc={datetime.now(timezone.utc).isoformat()}",
        "compute_device=CPU",
        "dtype=float64",
        f"observations={len(config['images']) * len(config['sigmas']) * len(config['seeds'])}",
        f"solver_trajectories={len(terminal_durations)}",
        f"metrics_rows={len(data.records)}",
        f"summary_rows={len(summary)}",
        f"latex_table_rows={latex_rows}",
        f"terminal_solver_time_sum_seconds={sum(terminal_durations):.9f}",
        f"whole_pipeline_wall_time_seconds={elapsed:.9f}",
        f"figure_files={len(figure_paths)}",
        "noise_and_solver_outputs_clipped=false",
        "display_clipped_to_unit_range=true",
    ]
    (destination / "run.log").write_text(
        "\n".join(log_lines) + "\n", encoding="utf-8"
    )
    if config["experiment_name"] == "extended":
        write_result_manifest(destination, config["experiment_name"])
    return {
        "experiment_name": config["experiment_name"],
        "metrics_rows": len(data.records),
        "summary_rows": len(summary),
        "solver_trajectories": len(terminal_durations),
        "figure_paths": [str(path) for path in figure_paths],
        "whole_pipeline_wall_time_seconds": elapsed,
        "terminal_solver_time_sum_seconds": sum(terminal_durations),
        "extended_analysis": extended_analysis,
    }
