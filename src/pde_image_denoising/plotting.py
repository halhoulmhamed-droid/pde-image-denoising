"""Matplotlib figures for the approved quick experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .boundaries import FloatArray
from .experiments import float_token


def _save_pair(figure: plt.Figure, directory: Path, stem: str) -> list[Path]:
    paths = [directory / f"{stem}.png", directory / f"{stem}.pdf"]
    figure.savefig(paths[0], dpi=180, bbox_inches="tight")
    figure.savefig(paths[1], bbox_inches="tight")
    plt.close(figure)
    return paths


def _selected_key(conduction: str, K: float, checkpoint: int) -> str:
    return f"pm_{conduction}_K{float_token(K)}_n{checkpoint}"


def _show_image(axis: plt.Axes, image: FloatArray, title: str) -> None:
    axis.imshow(image, cmap="gray", vmin=0.0, vmax=1.0, interpolation="nearest")
    axis.set_title(title)
    axis.set_axis_off()


def comparison_figure(
    arrays: dict[str, FloatArray], config: dict[str, Any]
) -> plt.Figure:
    representative = config["representative"]
    checkpoint = int(representative["checkpoint"])
    K = float(representative["K"])
    panels = [
        ("truth", "Propre"),
        ("noisy", "Bruitée"),
        (f"heat_n{checkpoint}", f"Chaleur, n={checkpoint}"),
        (
            _selected_key("exponential", K, checkpoint),
            f"PM exp., K={K:g}",
        ),
        (
            _selected_key("rational", K, checkpoint),
            f"PM rat., K={K:g}",
        ),
    ]
    figure, axes = plt.subplots(1, len(panels), figsize=(15, 3.2))
    for axis, (key, title) in zip(axes, panels, strict=True):
        _show_image(axis, arrays[key], title)
    figure.suptitle(
        "Comparaison prédéfinie — affichage borné à [0,1], calculs non tronqués"
    )
    figure.tight_layout()
    return figure


def curves_figure(
    records: list[dict[str, Any]], config: dict[str, Any]
) -> plt.Figure:
    representative = config["representative"]
    selected = [
        row
        for row in records
        if row["image"] == representative["image"]
        and float(row["sigma"]) == float(representative["sigma"])
        and int(row["seed"]) == int(representative["seed"])
        and row["method"] != "noisy"
    ]
    series: dict[tuple[str, str, Any], list[dict[str, Any]]] = {}
    for row in selected:
        key = (row["method"], row["conduction"], row["K"])
        series.setdefault(key, []).append(row)

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
    for key, rows in series.items():
        rows.sort(key=lambda row: int(row["n"]))
        method, conduction, K = key
        label = "Chaleur" if method == "heat" else f"PM {conduction}, K={K:g}"
        times = [float(row["diffusion_time"]) for row in rows]
        axes[0].plot(times, [float(row["psnr"]) for row in rows], marker="o", label=label)
        axes[1].plot(times, [float(row["ssim"]) for row in rows], marker="o", label=label)
    axes[0].set_ylabel("PSNR (dB)")
    axes[1].set_ylabel("SSIM")
    for axis in axes:
        axis.set_xlabel("Temps de diffusion n·dt")
        axis.grid(alpha=0.25)
    axes[1].legend(fontsize=8, loc="best")
    figure.suptitle("Métriques au cours de la diffusion — cas représentatif fixé")
    figure.tight_layout()
    return figure


def k_comparison_figure(
    arrays: dict[str, FloatArray], config: dict[str, Any]
) -> plt.Figure:
    checkpoint = int(config["representative"]["checkpoint"])
    panels: list[tuple[str, str]] = [("truth", "Propre"), ("noisy", "Bruitée")]
    for conduction in config["perona_malik"]["conductions"]:
        for K in config["perona_malik"]["K_values"]:
            panels.append(
                (
                    _selected_key(conduction, float(K), checkpoint),
                    f"{conduction}, K={float(K):g}",
                )
            )
    columns = 3
    rows = int(np.ceil(len(panels) / columns))
    figure, axes = plt.subplots(rows, columns, figsize=(10, 3.2 * rows))
    flat_axes = np.asarray(axes).ravel()
    for axis, (key, title) in zip(flat_axes, panels, strict=False):
        _show_image(axis, arrays[key], title)
    for axis in flat_axes[len(panels) :]:
        axis.set_axis_off()
    figure.suptitle(f"Valeurs de K prédéfinies à n={checkpoint}")
    figure.tight_layout()
    return figure


def profile_figure(
    arrays: dict[str, FloatArray], config: dict[str, Any]
) -> plt.Figure:
    representative = config["representative"]
    checkpoint = int(representative["checkpoint"])
    K = float(representative["K"])
    row_index = arrays["truth"].shape[0] // 3
    series = [
        ("truth", "Propre"),
        ("noisy", "Bruitée"),
        (f"heat_n{checkpoint}", "Chaleur"),
        (_selected_key("exponential", K, checkpoint), "PM exponentielle"),
        (_selected_key("rational", K, checkpoint), "PM rationnelle"),
    ]
    figure, axis = plt.subplots(figsize=(10, 4.4))
    for key, label in series:
        axis.plot(arrays[key][row_index, :], label=label, linewidth=1.4)
    axis.set_xlabel("Colonne (pixel)")
    axis.set_ylabel("Intensité non tronquée")
    axis.set_title(f"Profil horizontal — ligne {row_index}")
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    figure.tight_layout()
    return figure


def _gradient_magnitude(image: FloatArray, *, dx: float, dy: float) -> FloatArray:
    vertical, horizontal = np.gradient(image, float(dy), float(dx))
    return np.hypot(horizontal, vertical)


def gradient_figure(
    arrays: dict[str, FloatArray], config: dict[str, Any]
) -> plt.Figure:
    representative = config["representative"]
    checkpoint = int(representative["checkpoint"])
    K = float(representative["K"])
    keys = [
        ("truth", "Propre"),
        ("noisy", "Bruitée"),
        (f"heat_n{checkpoint}", "Chaleur"),
        (_selected_key("exponential", K, checkpoint), "PM exponentielle"),
        (_selected_key("rational", K, checkpoint), "PM rationnelle"),
    ]
    gradients = [
        _gradient_magnitude(
            arrays[key], dx=float(config["dx"]), dy=float(config["dy"])
        )
        for key, _ in keys
    ]
    shared_max = max(float(np.percentile(value, 99.0)) for value in gradients)
    figure = plt.figure(figsize=(15, 3.2))
    grid = figure.add_gridspec(
        1,
        len(keys) + 1,
        width_ratios=[1.0] * len(keys) + [0.045],
        wspace=0.12,
    )
    axes = [figure.add_subplot(grid[0, index]) for index in range(len(keys))]
    colorbar_axis = figure.add_subplot(grid[0, -1])
    image_handle = None
    for axis, gradient, (_, title) in zip(axes, gradients, keys, strict=True):
        image_handle = axis.imshow(
            gradient,
            cmap="magma",
            vmin=0.0,
            vmax=shared_max,
            interpolation="nearest",
        )
        axis.set_title(title)
        axis.set_axis_off()
    if image_handle is not None:
        figure.colorbar(image_handle, cax=colorbar_axis)
    figure.suptitle("Norme du gradient pour la visualisation — échelle partagée")
    figure.subplots_adjust(left=0.02, right=0.98, bottom=0.04, top=0.82)
    return figure


def generate_quick_figures(
    directory: Path,
    config: dict[str, Any],
    records: list[dict[str, Any]],
    arrays: dict[str, FloatArray],
) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    outputs += _save_pair(comparison_figure(arrays, config), directory, "comparison")
    outputs += _save_pair(curves_figure(records, config), directory, "metric_curves")
    outputs += _save_pair(k_comparison_figure(arrays, config), directory, "k_comparison")
    outputs += _save_pair(profile_figure(arrays, config), directory, "intensity_profile")
    outputs += _save_pair(gradient_figure(arrays, config), directory, "gradient_maps")
    return outputs
