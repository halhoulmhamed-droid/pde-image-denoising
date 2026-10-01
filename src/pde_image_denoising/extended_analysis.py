"""CSV-derived figures and tables for the predeclared phase-4 study.

Every plotted centre and band is taken from summary.csv: the centre is the
mean over seeds and the band is one sample standard deviation (ddof=1).
Ground-truth-based maxima are reported only as exploratory oracle choices.
No solver is called and no metric definition is changed here.
"""

from __future__ import annotations

import csv
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .experiments import METRICS_FIELDS, SUMMARY_FIELDS, float_token

CsvRow = dict[str, str]
SeriesKey = tuple[str, str, str]


def read_analysis_csv(path: Path, fields: list[str]) -> list[CsvRow]:
    """Read the recorded CSV with its exact schema, without recomputation."""
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != fields:
            raise ValueError(f"unexpected CSV schema in {path.name}")
        rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError(f"empty or malformed CSV: {path.name}")
    return rows


def select_case_rows(
    rows: list[CsvRow], image: str, sigma: float
) -> list[CsvRow]:
    return [
        row for row in rows
        if row["image"] == image and float(row["sigma"]) == float(sigma)
    ]


def _series_key(row: CsvRow) -> SeriesKey:
    return row["method"], row["conduction"], row["K"]


def _configuration_key(row: CsvRow) -> tuple[str, str, str, int]:
    return *_series_key(row), int(row["n"])


def grouped_metric_curves(
    case_rows: list[CsvRow], metric: str
) -> dict[SeriesKey, dict[str, list[float]]]:
    """Expose CSV means/sample dispersions and diffusion times for plotting."""
    if metric not in {"psnr", "ssim"}:
        raise ValueError("curve metric must be psnr or ssim")
    groups: dict[SeriesKey, list[CsvRow]] = {}
    for row in case_rows:
        if row["method"] != "noisy":
            groups.setdefault(_series_key(row), []).append(row)
    result = {}
    for key, rows in groups.items():
        ordered = sorted(rows, key=lambda row: int(row["n"]))
        if len({int(row["n"]) for row in ordered}) != len(ordered):
            raise ValueError("duplicate checkpoint in a metric curve")
        result[key] = {
            "time": [float(row["diffusion_time"]) for row in ordered],
            "mean": [float(row[f"{metric}_mean"]) for row in ordered],
            "std": [float(row[f"{metric}_std"]) for row in ordered],
        }
    return result


def sensitivity_checkpoints(config: dict[str, Any]) -> list[int]:
    positive = [int(n) for n in config["checkpoints"] if int(n) > 0]
    if not positive:
        raise ValueError("extended analysis requires a positive checkpoint")
    selected = [n for n in (5, 20, 80) if n in positive]
    return selected or [max(positive)]


def _series_label(key: SeriesKey) -> str:
    method, conduction, K = key
    if method == "heat":
        return "Chaleur"
    short = {"exponential": "exp.", "rational": "rat."}[conduction]
    return f"PM {short}, K={float(K):g}"


def _series_style(key: SeriesKey, config: dict[str, Any]) -> dict[str, Any]:
    if key[0] == "heat":
        return {"color": "black", "linestyle": "-", "linewidth": 2.0}
    K_values = [float(K) for K in config["perona_malik"]["K_values"]]
    index = K_values.index(float(key[2]))
    shade = float(np.linspace(0.4, 0.9, len(K_values))[index])
    return {
        "color": plt.get_cmap("Blues" if key[1] == "exponential" else "Oranges")(
            shade
        ),
        "linestyle": "-" if key[1] == "exponential" else "--",
        "linewidth": 1.6,
    }


def _baseline(axis: plt.Axes, rows: list[CsvRow], metric: str) -> None:
    noisy = [row for row in rows if row["method"] == "noisy"]
    if len(noisy) != 1:
        raise ValueError("each image/sigma case requires one noisy summary row")
    mean = float(noisy[0][f"{metric}_mean"])
    std = float(noisy[0][f"{metric}_std"])
    axis.axhline(mean, color="0.45", linestyle=":", label="Bruitée (référence)")
    axis.axhspan(mean - std, mean + std, color="0.45", alpha=0.06)


def _finish_case_figure(
    figure: plt.Figure, axes: np.ndarray, image: str, sigma: float, n_seeds: int,
    title: str,
) -> None:
    axes[0].set_ylabel("PSNR (dB)")
    axes[1].set_ylabel("SSIM")
    for axis, metric_title in zip(axes, ("PSNR", "SSIM"), strict=True):
        axis.set_title(metric_title)
        axis.grid(alpha=0.25)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=3, fontsize=8.5)
    figure.suptitle(
        f"{title}\n{image}, σ={sigma:g}, {n_seeds} graine(s) — moyenne ± écart-type"
    )
    figure.tight_layout(rect=(0.0, 0.23, 1.0, 0.9))


def metric_curves_figure(
    case_rows: list[CsvRow], config: dict[str, Any], image: str, sigma: float
) -> plt.Figure:
    figure, axes = plt.subplots(1, 2, figsize=(13.0, 6.8), sharex=True)
    for axis, metric in zip(axes, ("psnr", "ssim"), strict=True):
        for key, values in grouped_metric_curves(case_rows, metric).items():
            mean, std = np.asarray(values["mean"]), np.asarray(values["std"])
            style = _series_style(key, config)
            axis.plot(
                values["time"], mean, marker="o", markersize=3,
                label=_series_label(key), **style,
            )
            axis.fill_between(
                values["time"], mean - std, mean + std,
                color=style["color"], alpha=0.08,
            )
        _baseline(axis, case_rows, metric)
        axis.set_xlabel("Temps de diffusion t = n·dt (convention pixel)")
    _finish_case_figure(
        figure, axes, image, sigma, int(case_rows[0]["n_seeds"]),
        "Évolution à paramètres fixés — toutes les valeurs de K prédéfinies",
    )
    return figure


def k_sensitivity_figure(
    case_rows: list[CsvRow], config: dict[str, Any], image: str, sigma: float
) -> plt.Figure:
    checkpoints = sensitivity_checkpoints(config)
    K_values = sorted(float(K) for K in config["perona_malik"]["K_values"])
    figure, axes = plt.subplots(1, 2, figsize=(13.0, 6.8), sharex=True)
    colors = plt.get_cmap("viridis")(np.linspace(0.15, 0.85, len(checkpoints)))
    for axis, metric in zip(axes, ("psnr", "ssim"), strict=True):
        for checkpoint, color in zip(checkpoints, colors, strict=True):
            for conduction in config["perona_malik"]["conductions"]:
                selected = sorted(
                    [row for row in case_rows if row["method"] == "perona_malik"
                     and row["conduction"] == conduction
                     and int(row["n"]) == checkpoint],
                    key=lambda row: float(row["K"]),
                )
                if [float(row["K"]) for row in selected] != K_values:
                    raise ValueError("missing K value in sensitivity plot")
                means = np.asarray([float(row[f"{metric}_mean"]) for row in selected])
                stds = np.asarray([float(row[f"{metric}_std"]) for row in selected])
                short = "exp." if conduction == "exponential" else "rat."
                axis.errorbar(
                    K_values, means, yerr=stds, capsize=3, color=color,
                    linestyle="-" if conduction == "exponential" else "--",
                    marker="o" if conduction == "exponential" else "s",
                    markersize=4, label=f"PM {short}, n={checkpoint}",
                )
            heat = [row for row in case_rows if row["method"] == "heat"
                    and int(row["n"]) == checkpoint]
            if len(heat) != 1:
                raise ValueError("missing heat baseline in sensitivity plot")
            axis.axhline(
                float(heat[0][f"{metric}_mean"]), color=color, linestyle=":",
                linewidth=1.2, label=f"Chaleur, n={checkpoint}",
            )
        _baseline(axis, case_rows, metric)
        axis.set_xscale("log", base=2)
        axis.set_xticks(K_values, [f"{value:g}" for value in K_values])
        axis.set_xlabel("Seuil K (échelle logarithmique)")
    _finish_case_figure(
        figure, axes, image, sigma, int(case_rows[0]["n_seeds"]),
        f"Sensibilité à K — checkpoints communs {checkpoints}",
    )
    return figure


def common_checkpoint_rows(
    summary: list[CsvRow], config: dict[str, Any]
) -> list[CsvRow]:
    """All predefined variants at all positive checkpoints, plus noisy baseline."""
    output = []
    for image in config["images"]:
        for sigma in config["sigmas"]:
            case = select_case_rows(summary, image, float(sigma))
            for checkpoint in config["checkpoints"]:
                if int(checkpoint) <= 0:
                    continue
                selected = [row for row in case if row["method"] == "noisy"
                            or int(row["n"]) == int(checkpoint)]
                for row in selected:
                    output.append({"comparison_n": str(checkpoint), **row})
    return output


def _write_csv(path: Path, rows: list[CsvRow], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_escape(value: str) -> str:
    return value.replace("\\", r"\textbackslash{}").replace("_", r"\_").replace(
        "%", r"\%"
    ).replace("&", r"\&")


def _latex_statistic(row: CsvRow, metric: str) -> str:
    return (
        f"${float(row[f'{metric}_mean']):.5g} "
        f"\\pm {float(row[f'{metric}_std']):.3g}$"
    )


def write_common_checkpoint_latex(csv_path: Path, output_path: Path) -> int:
    """Read the generated CSV; report every variant without oracle filtering."""
    fields = ["comparison_n", *SUMMARY_FIELDS]
    rows = read_analysis_csv(csv_path, fields)
    groups: dict[tuple[str, str, str], list[CsvRow]] = {}
    for row in rows:
        groups.setdefault((row["image"], row["sigma"], row["comparison_n"]), []).append(row)
    lines = [
        "% Generated from extended_common_checkpoints.csv; means and sample standard deviations.",
        "% Requires booktabs and graphicx. Each table uses the same checkpoint budget.",
        "% Noisy n=0 is repeated as a common baseline, not evolved to comparison_n.",
    ]
    for (image, sigma, checkpoint), group in groups.items():
        lines += [
            r"\par\medskip\noindent",
            f"{_latex_escape(image)}, $\\sigma={float(sigma):g}$, "
            f"$n={checkpoint}$, {group[0]['n_seeds']} graines.",
            r"\par\smallskip\noindent\resizebox{\textwidth}{!}{%",
            r"\begin{tabular}{lllrrrrr}", r"\toprule",
            r"Méthode & Conduction / $K$ & $n$ & MSE & L2 rel. & PSNR (dB) & SSIM & Durée (s) \\",
            r"\midrule",
        ]
        for row in group:
            method = {"noisy": "Bruitée", "heat": "Chaleur",
                      "perona_malik": "Perona--Malik"}[row["method"]]
            detail = "--" if row["method"] != "perona_malik" else (
                f"{row['conduction']} / {float(row['K']):g}"
            )
            statistics = " & ".join(
                _latex_statistic(row, metric) for metric in
                ("mse", "relative_l2", "psnr", "ssim", "duration_seconds")
            )
            lines.append(
                f"{method} & {_latex_escape(detail)} & {row['n']} & "
                f"{statistics} \\\\"
            )
        lines += [r"\bottomrule", r"\end{tabular}%", "}", ""]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


def oracle_and_rankings(
    summary: list[CsvRow], config: dict[str, Any]
) -> tuple[list[CsvRow], dict[str, Any]]:
    """Compare aggregate ranks, explicitly marking ground-truth oracle use."""
    oracle_rows: list[CsvRow] = []
    fixed_comparisons: list[dict[str, Any]] = []
    oracle_case_disagreements = 0
    for image in config["images"]:
        for sigma in config["sigmas"]:
            candidates = [row for row in select_case_rows(summary, image, float(sigma))
                          if row["method"] != "noisy" and int(row["n"]) > 0]
            if not candidates:
                raise ValueError("no positive-checkpoint candidate for oracle table")
            winners = {}
            for metric in ("psnr", "ssim"):
                winner = max(candidates, key=lambda row: float(row[f"{metric}_mean"]))
                winners[metric] = winner
                oracle_rows.append({"oracle_criterion": metric, **winner})
            oracle_case_disagreements += (
                _configuration_key(winners["psnr"]) != _configuration_key(winners["ssim"])
            )
            for checkpoint in config["checkpoints"]:
                if int(checkpoint) <= 0:
                    continue
                selected = [row for row in candidates if int(row["n"]) == int(checkpoint)]
                ordered = {
                    metric: sorted(selected, key=lambda row: float(row[f"{metric}_mean"]),
                                   reverse=True)
                    for metric in ("psnr", "ssim")
                }
                discordant = 0
                compared_pairs = 0
                for first, second in combinations(selected, 2):
                    psnr_delta = float(first["psnr_mean"]) - float(second["psnr_mean"])
                    ssim_delta = float(first["ssim_mean"]) - float(second["ssim_mean"])
                    if psnr_delta != 0.0 and ssim_delta != 0.0:
                        compared_pairs += 1
                        discordant += (psnr_delta * ssim_delta < 0.0)
                fixed_comparisons.append({
                    "image": image, "sigma": float(sigma), "n": int(checkpoint),
                    "diffusion_time": int(checkpoint) * float(config["dt"]),
                    "psnr_ranking": [list(_series_key(row)) for row in ordered["psnr"]],
                    "ssim_ranking": [list(_series_key(row)) for row in ordered["ssim"]],
                    "top_configuration_differs": (
                        _series_key(ordered["psnr"][0]) != _series_key(ordered["ssim"][0])
                    ),
                    "discordant_pairs": int(discordant),
                    "non_tied_pairs_compared": compared_pairs,
                })
    report = {
        "selection_label": "oracle exploratoire",
        "selection_rule": (
            "Maximum of a ground-truth metric mean over the configured seeds, "
            "among all predefined solver/K/checkpoint combinations with n>0; "
            "ties use the first summary.csv row. This is not a deployable selection rule."
        ),
        "dispersion": "sample standard deviation over seeds (ddof=1); not a confidence interval",
        "oracle_case_count": len(oracle_rows) // 2,
        "oracle_psnr_ssim_configuration_disagreements": int(oracle_case_disagreements),
        "fixed_checkpoint_comparison_count": len(fixed_comparisons),
        "fixed_checkpoint_top_disagreements": sum(
            row["top_configuration_differs"] for row in fixed_comparisons
        ),
        "fixed_checkpoint_discordant_pairs": sum(
            row["discordant_pairs"] for row in fixed_comparisons
        ),
        "fixed_checkpoint_non_tied_pairs": sum(
            row["non_tied_pairs_compared"] for row in fixed_comparisons
        ),
        "fixed_checkpoint_comparisons": fixed_comparisons,
    }
    return oracle_rows, report


def write_oracle_latex(csv_path: Path, output_path: Path) -> int:
    rows = read_analysis_csv(csv_path, ["oracle_criterion", *SUMMARY_FIELDS])
    lines = [
        "% Generated from oracle_exploratory.csv; selection uses the ground truth.",
        r"\noindent Choix oracle exploratoire : maximum de la moyenne sur les graines.",
        r"\par\smallskip\noindent\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lllrllrr}", r"\toprule",
        r"Image & $\sigma$ & Critère & $n$ & Méthode & Conduction / $K$ & PSNR & SSIM \\",
        r"\midrule",
    ]
    for row in rows:
        detail = "--" if row["method"] == "heat" else (
            f"{row['conduction']} / {float(row['K']):g}"
        )
        lines.append(
            f"{_latex_escape(row['image'])} & {float(row['sigma']):g} & "
            f"{row['oracle_criterion'].upper()} & {row['n']} & "
            f"{_latex_escape(row['method'])} & {_latex_escape(detail)} & "
            f"{_latex_statistic(row, 'psnr')} & {_latex_statistic(row, 'ssim')} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}%", "}"]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


def _save_pair(figure: plt.Figure, directory: Path, stem: str) -> list[Path]:
    paths = [directory / f"{stem}.png", directory / f"{stem}.pdf"]
    figure.savefig(paths[0], dpi=180, bbox_inches="tight")
    figure.savefig(paths[1], bbox_inches="tight")
    plt.close(figure)
    return paths


def generate_extended_analysis(directory: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Generate phase-4 analysis from existing CSV files only."""
    directory = Path(directory)
    records = read_analysis_csv(directory / "metrics.csv", METRICS_FIELDS)
    summary = read_analysis_csv(directory / "summary.csv", SUMMARY_FIELDS)
    figures_dir, tables_dir = directory / "figures", directory / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures = []
    for image in config["images"]:
        for sigma in config["sigmas"]:
            case = select_case_rows(summary, image, float(sigma))
            if not case or {int(row["n_seeds"]) for row in case} != {len(config["seeds"])}:
                raise ValueError("missing case or inconsistent seed count in analysis summary")
            stem = f"{image}_sigma{float_token(float(sigma))}"
            figures += _save_pair(
                metric_curves_figure(case, config, image, float(sigma)),
                figures_dir, f"metric_curves_{stem}",
            )
            figures += _save_pair(
                k_sensitivity_figure(case, config, image, float(sigma)),
                figures_dir, f"k_sensitivity_{stem}",
            )
    checkpoint_csv = tables_dir / "extended_common_checkpoints.csv"
    checkpoint_tex = tables_dir / "extended_common_checkpoints.tex"
    _write_csv(checkpoint_csv, common_checkpoint_rows(summary, config),
               ["comparison_n", *SUMMARY_FIELDS])
    common_rows = write_common_checkpoint_latex(checkpoint_csv, checkpoint_tex)
    oracle_rows, report = oracle_and_rankings(summary, config)
    oracle_csv = tables_dir / "oracle_exploratory.csv"
    oracle_tex = tables_dir / "oracle_exploratory.tex"
    _write_csv(oracle_csv, oracle_rows, ["oracle_criterion", *SUMMARY_FIELDS])
    write_oracle_latex(oracle_csv, oracle_tex)
    report.update({
        "source_metrics_csv": "metrics.csv", "source_summary_csv": "summary.csv",
        "source_metrics_rows": len(records), "source_summary_rows": len(summary),
        "common_checkpoint_rows": common_rows, "oracle_rows": len(oracle_rows),
        "sensitivity_checkpoints": sensitivity_checkpoints(config),
        "curve_cases": len(config["images"]) * len(config["sigmas"]),
        "figure_paths": [str(path) for path in figures],
        "table_paths": [str(path) for path in
                        (checkpoint_csv, checkpoint_tex, oracle_csv, oracle_tex)],
    })
    report_path = directory / "analysis.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    return {**report, "analysis_report_path": str(report_path)}
