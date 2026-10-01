"""Export documentary tables from archived CSV/JSON, without scientific code.

Default: write only report/generated. --check: compare every export in memory
with the existing files, read-only. No solver, runner, plotting or metric import.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
import math
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results" / "extended"
DESTINATION = ROOT / "report" / "generated"
GROUP_FIELDS = ["image", "sigma", "method", "conduction", "K", "dx", "dy", "dt", "n", "diffusion_time"]
VALUE_FIELDS = ["mse", "relative_l2", "psnr", "ssim", "duration_seconds"]
SUMMARY_FIELDS = GROUP_FIELDS + ["n_seeds"] + [item for value in VALUE_FIELDS for item in (f"{value}_mean", f"{value}_std")]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    if not fields or not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError(f"Malformed or empty archived CSV: {path}")
    return fields, rows


def number(value: str, digits: int = 4) -> str:
    numeric = float(value)
    if math.isnan(numeric):
        raise ValueError("NaN is not a documentary value")
    if not math.isfinite(numeric):
        return r"\infty" if numeric > 0 else r"-\infty"
    return f"{numeric:.{digits}f}"


def scientific(value: float, digits: int = 8) -> str:
    mantissa, exponent = f"{value:.{digits}e}".split("e")
    return rf"{mantissa}\times10^{{{int(exponent)}}}"


def statistic(row: dict[str, str], metric: str, digits: int = 4) -> str:
    deviation = float(row[metric + "_std"])
    if 0 < abs(deviation) < 0.5 * 10 ** (-digits):
        mantissa, exponent = f"{deviation:.2e}".split("e")
        displayed_std = rf"{mantissa}\times10^{{{int(exponent)}}}"
    else:
        displayed_std = number(row[metric + "_std"], digits)
    return f"${number(row[metric + '_mean'], digits)} \\pm {displayed_std}$"


def method(row: dict[str, str]) -> str:
    return {"noisy": "Bruitée", "heat": "Chaleur", "perona_malik": "PM exp." if row["conduction"] == "exponential" else "PM rat."}[row["method"]]


def key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row[field] for field in GROUP_FIELDS)


def csv_content(fields: list[str], rows: list[dict[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def table(rows: list[dict[str, str]], *, configuration: bool = False, oracle: bool = False) -> str:
    lines = ["% Generated from archived summary.csv; rounding applies only to display."]
    if oracle:
        lines += [r"\begin{tabular}{lllrll}", r"\toprule", r"Image / $\sigma$ & Méthode & $K$ & $n$ & PSNR (dB) & SSIM \\"]
    elif configuration:
        lines += [r"\begin{tabular}{llrll}", r"\toprule", r"Méthode & $K$ & $n$ & PSNR (dB) & SSIM \\"]
    else:
        lines += [r"\begin{tabular}{lll}", r"\toprule", r"Méthode & PSNR (dB) & SSIM \\"]
    lines.append(r"\midrule")
    for row in rows:
        cells = []
        if oracle:
            image = "Géométrique" if row["image"] == "geometric_shapes" else "Rampe"
            cells.append(f"{image} / {row['sigma']}")
        cells.append(method(row))
        if configuration or oracle:
            cells += [row["K"] if row["K"] else "--", row["n"]]
        cells += [statistic(row, "psnr"), statistic(row, "ssim")]
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


def build_material() -> tuple[dict[str, str], dict[str, int]]:
    fields, summary = read_csv(ARCHIVE / "summary.csv")
    _, records = read_csv(ARCHIVE / "metrics.csv")
    assert fields == SUMMARY_FIELDS
    assert len(summary) == 438 and len(records) == 4380
    configuration = json.loads((ARCHIVE / "config_used.json").read_text("utf-8"))
    environment = json.loads((ARCHIVE / "environment.json").read_text("utf-8"))
    verification = json.loads((ARCHIVE / "verification.json").read_text("utf-8"))
    analysis = json.loads((ARCHIVE / "analysis.json").read_text("utf-8"))
    assert configuration["seeds"] == list(range(10))
    assert configuration == json.loads((ROOT / "configs" / "extended.json").read_text("utf-8"))
    assert verification["status"] == "passed" and verification["verification_mode"] == "strict"
    groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in records:
        groups.setdefault(key(row), []).append(row)
    assert len(groups) == len(summary)
    indexed = {key(row): row for row in summary}
    assert len(indexed) == len(summary) and set(indexed) == set(groups)
    for group_key, rows in groups.items():
        aggregate = indexed[group_key]
        assert {int(row["seed"]) for row in rows} == set(range(10)) and len(rows) == 10
        assert int(aggregate["n_seeds"]) == 10
        assert len({row["noisy_sha256"] for row in rows}) == 10
        for metric in VALUE_FIELDS:
            values = [float(row[metric]) for row in rows]
            assert float(aggregate[metric + "_mean"]) == statistics.fmean(values)
            assert float(aggregate[metric + "_std"]) == statistics.stdev(values)
    shared_observations: dict[tuple[str, str, str], set[str]] = {}
    for row in records:
        shared_observations.setdefault((row["image"], row["sigma"], row["seed"]), set()).add(row["noisy_sha256"])
    assert len(shared_observations) == 60 and all(len(values) == 1 for values in shared_observations.values())

    def select(image="geometric_shapes", sigma="0.1", n=20):
        return [row for row in summary if row["image"] == image and Decimal(row["sigma"]) == Decimal(sigma) and (row["method"] == "noisy" or int(row["n"]) == n)]

    common = select()
    fixed = [row for row in common if row["method"] != "perona_malik" or Decimal(row["K"]) == Decimal("0.1")]
    order = {("noisy", ""): 0, ("heat", ""): 1, ("perona_malik", "exponential"): 2, ("perona_malik", "rational"): 3}
    fixed.sort(key=lambda row: order[(row["method"], row["conduction"])])
    assert len(fixed) == 4 and len(common) == 10
    time_rows = [row for row in summary if row["image"] == "geometric_shapes" and Decimal(row["sigma"]) == Decimal("0.1") and int(row["n"]) in (2, 5, 20, 80) and (row["method"] == "heat" or (row["method"] == "perona_malik" and ((row["conduction"] == "rational" and row["K"] in ("0.1", "0.2")) or (row["conduction"] == "exponential" and row["K"] == "0.2"))))]
    assert len(time_rows) == 16
    _, archived_oracles = read_csv(ARCHIVE / "tables" / "oracle_exploratory.csv")
    oracles = [{field: row[field] for field in fields} for row in archived_oracles if row["oracle_criterion"] == "psnr"]
    difference = [{field: row[field] for field in fields} for row in archived_oracles if row["image"] == "ramps_and_edges" and Decimal(row["sigma"]) == Decimal("0.1")]
    assert len(oracles) == 6 and len(difference) == 2
    for archived in archived_oracles:
        candidate = {field: archived[field] for field in fields}
        assert candidate == indexed[key(candidate)]
        choices = [row for row in summary if row["image"] == candidate["image"] and row["sigma"] == candidate["sigma"] and row["method"] != "noisy" and int(row["n"]) > 0]
        criterion = archived["oracle_criterion"] + "_mean"
        assert float(candidate[criterion]) == max(float(row[criterion]) for row in choices)
    selections = {"fixed_case": fixed, "common_n20": common, "time_case": time_rows, "oracle_psnr": oracles, "oracle_ssim_difference": difference, "exhaustive": summary}
    material = {}
    provenance = {}
    line_numbers = {key(row): number for number, row in enumerate(summary, 2)}
    for name, rows in selections.items():
        material[name + ".csv"] = csv_content(fields, rows)
        provenance[name] = [{"source_file": "results/extended/summary.csv", "source_line": line_numbers[key(row)], "values": row} for row in rows]
        if name != "exhaustive":
            material[name + ".tex"] = table(rows, configuration=name in {"common_n20", "time_case", "oracle_ssim_difference"}, oracle=name == "oracle_psnr")
    material["slides_fixed_case.tex"] = table(fixed)
    macro_lines = ["% Generated from the fixed-case source rows; not manually entered."]
    for row, prefix in zip(fixed, ("Noisy", "Heat", "Exp", "Rat"), strict=True):
        for metric, suffix in (("psnr", "PSNR"), ("ssim", "SSIM")):
            macro_lines.append(f"\\newcommand{{\\{prefix}{suffix}}}{{{number(row[metric + '_mean'], 6)}}}")
    material["slides_fixed_values.tex"] = "\n".join(macro_lines) + "\n"
    exhaustive = ["% All 438 archived summary groups, including n=0; sample SD, ten seeds."]
    for image in configuration["images"]:
        for sigma in configuration["sigmas"]:
            rows = [row for row in summary if row["image"] == image and Decimal(row["sigma"]) == Decimal(str(sigma))]
            caption = ("Régions géométriques" if image == "geometric_shapes" else "Rampe et contours") + f", $\\sigma={sigma:g}$ : grille complète, moyennes $\\pm$ écarts-types sur dix graines."
            exhaustive += [r"\begin{longtable}{llrll}", f"\\caption{{{caption}}}\\\\", r"\toprule", r"Méthode & $K$ & $n$ & PSNR (dB) & SSIM \\", r"\midrule", r"\endfirsthead", r"\toprule", r"Méthode & $K$ & $n$ & PSNR (dB) & SSIM \\", r"\midrule", r"\endhead", r"\bottomrule", r"\endfoot"]
            for row in rows:
                exhaustive.append(" & ".join([method(row), row["K"] or "--", row["n"], statistic(row, "psnr"), statistic(row, "ssim")]) + r" \\")
            exhaustive += [r"\end{longtable}", ""]
    material["exhaustive.tex"] = "\n".join(exhaustive) + "\n"
    verification_lines = [r"\begin{tabular}{lll}", r"\toprule", r"Contrôle & Niveau & Erreur d'amplitude ou maximale \\", r"\midrule"]
    error = verification["heat_discrete_neumann_mode"]["max_abs_error"]
    verification_lines.append(f"Mode propre discret & $17\\times19$, 7 pas & ${scientific(error)}$" + r" \\")
    for source_key, label in (("spatial_semidiscrete_vs_continuous_amplitude_errors", "Spatial"), ("temporal_euler_vs_semidiscrete_amplitude_errors", "Temporel")):
        for level, value in verification["refinement_checks"][source_key].items():
            verification_lines.append(f"{label} & {level} & ${scientific(value)}$" + r" \\")
    verification_lines += [r"\bottomrule", r"\end{tabular}"]
    material["verification.tex"] = "\n".join(verification_lines) + "\n"
    environment_lines = [r"\begin{tabular}{ll}", r"\toprule", r"Élément & Valeur enregistrée \\", r"\midrule", f"Python & {environment['python'].split()[0]}" + r" \\", f"Plateforme & {environment['platform']}" + r" \\"]
    for package, version in environment["packages"].items():
        environment_lines.append(f"{package} & {version}" + r" \\")
    environment_lines += [f"Calcul & {environment['compute_device']}, {environment['numeric_dtype']}" + r" \\", r"\bottomrule", r"\end{tabular}"]
    material["environment.tex"] = "\n".join(environment_lines) + "\n"
    sources = ["results/extended/metrics.csv", "results/extended/summary.csv", "results/extended/config_used.json", "results/extended/environment.json", "results/extended/verification.json", "results/extended/analysis.json", "results/extended/tables/oracle_exploratory.csv"]
    provenance_payload = {"sources": {path: digest(ROOT / path) for path in sources}, "rounding": "Display only; CSV/JSON values retain source strings", "tables": provenance, "verification_values": verification["refinement_checks"], "ranking_counts": {field: analysis[field] for field in ("fixed_checkpoint_top_disagreements", "fixed_checkpoint_comparison_count", "fixed_checkpoint_discordant_pairs", "fixed_checkpoint_non_tied_pairs")}}
    material["source_values.json"] = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    return material, {"metrics_rows": len(records), "summary_rows": len(summary), "aggregate_statistics_checked": len(summary) * 10, "shared_observations": len(shared_observations), "exported_source_rows": sum(map(len, selections.values()))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only exact export/CSV correspondence check")
    arguments = parser.parse_args()
    material, counts = build_material()
    if arguments.check:
        differences = [name for name, content in material.items() if not (DESTINATION / name).is_file() or (DESTINATION / name).read_text("utf-8") != content]
        if differences:
            raise SystemExit("Documentary export mismatch: " + ", ".join(differences))
    else:
        DESTINATION.mkdir(parents=True, exist_ok=True)
        for name, content in material.items():
            (DESTINATION / name).write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "passed", "mode": "check" if arguments.check else "export", "scientific_calculations": False, "destination": str(DESTINATION), "files": len(material), **counts}, indent=2))


if __name__ == "__main__":
    main()
