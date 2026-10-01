"""Read-only, standard-library checks of phase-5 documentary sources.

Print a JSON report by default. --report additionally writes only one of
the two explicitly allowed phase-5 documentary JSON reports. This is a static check,
not a LaTeX compilation, PDF layout validation, or scientific test run.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import ast
from collections import Counter
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_DESTINATION = ROOT / "docs" / "phase5_documentary_checks.json"
V2_REPORT_DESTINATION = ROOT / "docs" / "phase5_v2_documentary_checks.json"
ALLOWED_REPORT_DESTINATIONS = {REPORT_DESTINATION.resolve(), V2_REPORT_DESTINATION.resolve()}
EXCLUDED_DIRECTORIES = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".cache", ".ipynb_checkpoints", "build", "dist",
}
PROTECTED_EXCLUDED_DIRECTORIES = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "build", "dist",
}
EXCLUDED_SUFFIXES = (
    ".pyc", ".pyo", ".tmp", ".temp", ".bak", ".swp", ".swo",
    ".aux", ".bbl", ".blg", ".out", ".toc", ".lof", ".lot", ".nav",
    ".snm", ".vrb", ".fls", ".fdb_latexmk", ".synctex.gz", ".dvi", ".xdv",
)
RAW_BUILD_LOG_DIRECTORY = "docs/phase5_v2_build/"
EXPECTED_SOURCES = {
    "results/extended/metrics.csv", "results/extended/summary.csv",
    "results/extended/config_used.json", "results/extended/environment.json",
    "results/extended/verification.json", "results/extended/analysis.json",
    "results/extended/tables/oracle_exploratory.csv",
}
DOCUMENTARY_TEXT_SUFFIXES = {
    ".md", ".tex", ".bib", ".py", ".json", ".csv", ".txt", ".toml", ".cff", ".log",
}
PLACEHOLDERS = re.compile(
    r"\b(?:TODO|FIXME|TBD|PLACEHOLDER)\b|\bà\s+(?:rédiger|compléter|développer)\b",
    re.IGNORECASE,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def project_path(value: str) -> Path:
    path = ROOT / value
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Path outside the project: {value}")
    return path


def ignored(path: Path) -> bool:
    return (
        any(part in EXCLUDED_DIRECTORIES or part.endswith(".egg-info")
            for part in path.relative_to(ROOT).parts)
        or path.name.lower().endswith(EXCLUDED_SUFFIXES)
        or (path.suffix.lower() == ".log" and path.name != "run.log")
    )


def inventory(directory: Path, *, documentary: bool = False) -> set[str]:
    """Keep protected-scope exclusions identical to the original baseline."""
    files: set[str] = set()
    directories_to_ignore = EXCLUDED_DIRECTORIES if documentary else PROTECTED_EXCLUDED_DIRECTORIES
    for current, directories, names in os.walk(directory, followlinks=False):
        directories[:] = [
            name for name in directories
            if name not in directories_to_ignore and not name.endswith(".egg-info")
        ]
        for name in names:
            path = Path(current) / name
            excluded = ignored(path) if documentary else path.suffix.lower() == ".pyc"
            if not excluded:
                files.add(relative(path))
    return files


def escaped(text: str, index: int) -> bool:
    preceding = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        preceding += 1
        index -= 1
    return preceding % 2 == 1


def clean_tex(text: str) -> str:
    """Mask comments and literal code, preserving line-number information."""
    literals = re.compile(
        r"\\begin\{(lstlisting\*?|verbatim\*?|Verbatim)\}.*?\\end\{\1\}",
        re.DOTALL,
    )
    text = literals.sub(lambda match: "\n" * match.group().count("\n"), text)
    text = re.sub(r"\\verb\*?([^\w\s])(.*?)\1", "", text)
    lines = []
    for line in text.splitlines(keepends=True):
        for index, character in enumerate(line):
            if character == "%" and not escaped(line, index):
                line = line[:index] + ("\n" if line.endswith("\n") else "")
                break
        lines.append(line)
    return "".join(lines)


class DocumentaryChecks:
    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.checks: dict[str, Any] = {}
        self.baseline: dict[str, dict[str, Any]] = {}
        self.script_imports_valid = False
        self.material: dict[str, str] = {}
        self.provenance: dict[str, Any] = {}
        self.summary: list[dict[str, str]] = []

    def error(self, check: str, message: str, path: str = "") -> None:
        self.errors.append({"check": check, "path": path, "message": message})

    def run_check(self, name: str, function: Any) -> None:
        try:
            function()
        except Exception as exception:
            self.error(name, f"{type(exception).__name__}: {exception}")

    def check_scripts(self) -> None:
        previous_errors = len(self.errors)
        paths = sorted((ROOT / "scripts").glob("*.py"))
        imports: dict[str, list[str]] = {}
        for path in paths:
            tree = ast.parse(path.read_text("utf-8"), filename=relative(path))
            modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        self.error("script_imports", "Relative imports are not allowed", relative(path))
                    modules.append(node.module or "")
            for module in modules:
                if module.split(".")[0] not in sys.stdlib_module_names | {"__future__"}:
                    self.error("script_imports", f"Non-stdlib import: {module}", relative(path))
            imports[relative(path)] = sorted(set(modules))
        if not paths:
            self.error("script_syntax", "No documentary scripts found")
        self.checks["script_ast_and_stdlib_imports"] = imports
        self.script_imports_valid = len(self.errors) == previous_errors

    def check_protection(self) -> None:
        before_path = ROOT / "docs" / "phase5_protection_before.json"
        payload = json.loads(before_path.read_text("utf-8"))
        entries = payload["files"]
        self.baseline = {entry["path"]: entry for entry in entries}
        if len(self.baseline) != len(entries):
            self.error("protection", "Duplicate protected paths in baseline")
        changed, missing = [], []
        for value, entry in self.baseline.items():
            path = project_path(value)
            if not path.is_file():
                missing.append(value)
            elif path.stat().st_size != entry["size_bytes"] or digest(path) != entry["sha256"]:
                changed.append(value)
        actual: set[str] = set()
        expected: set[str] = set()
        for value in payload["directories"]:
            directory = project_path(value)
            prefix = value.rstrip("/") + "/"
            expected.update(name for name in self.baseline if name.startswith(prefix))
            if directory.is_dir():
                actual.update(inventory(directory))
            else:
                self.error("protection", "Protected directory missing", value)
        added = sorted(actual - expected)
        removed = sorted(expected - actual)
        for name, values in (("changed", changed), ("missing", missing),
                             ("added", added), ("removed", removed)):
            for value in values:
                self.error("protection", f"Protected file {name}", value)
        self.checks["protected_files"] = {
            "baseline": relative(before_path), "count": len(entries),
            "directories": payload["directories"], "changed": changed,
            "missing": missing, "added": added, "removed": removed,
            "paths": sorted(self.baseline),
            "excluded": sorted(PROTECTED_EXCLUDED_DIRECTORIES) + ["*.egg-info", "*.pyc"],
        }

    def check_extended_manifest(self) -> None:
        """Hash/size/inventory only: no scientific verifier or metric call."""
        directory = ROOT / "results" / "extended"
        path = directory / "manifest.json"
        manifest = json.loads(path.read_text("utf-8"))
        if not isinstance(manifest, dict) or set(manifest) != {"experiment_name", "config_sha256", "files"}:
            raise ValueError("Invalid extended manifest schema")
        configuration = json.loads((directory / "config_used.json").read_text("utf-8"))
        if manifest["experiment_name"] != configuration["experiment_name"]:
            self.error("extended_manifest", "Experiment name differs from config_used.json")
        configuration_matches = manifest["config_sha256"] == digest(directory / "config_used.json")
        if not configuration_matches:
            self.error("extended_manifest", "Configuration SHA-256 differs")
        entries = manifest["files"]
        if not isinstance(entries, list) or len(entries) != 47:
            raise ValueError("The archived extended manifest must contain 47 entries")
        omitted = {"manifest.json", "verification.json", "verification_numerical.json"}
        listed: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size_bytes"}:
                raise ValueError("Invalid extended manifest entry schema")
            value = entry["path"]
            if not isinstance(value, str) or not value:
                raise ValueError("Manifest path must be a non-empty relative string")
            posix_path, windows_path = PurePosixPath(value), PureWindowsPath(value)
            if ("\\" in value or posix_path.is_absolute() or windows_path.drive or windows_path.root
                    or ".." in posix_path.parts or ":" in value
                    or posix_path.as_posix() != value or value in omitted):
                raise ValueError(f"Unsafe or reserved manifest path: {value}")
            if value in listed:
                raise ValueError(f"Duplicate manifest path: {value}")
            listed.add(value)
            artifact = directory.joinpath(*posix_path.parts)
            if not artifact.resolve().is_relative_to(directory.resolve()):
                raise ValueError(f"Manifest path escapes the results directory: {value}")
            expected_hash, expected_size = entry["sha256"], entry["size_bytes"]
            if not isinstance(expected_hash, str) or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None:
                raise ValueError(f"Invalid manifest hash: {value}")
            if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size < 0:
                raise ValueError(f"Invalid manifest size: {value}")
            if not artifact.is_file():
                self.error("extended_manifest", "Manifest artifact is missing", relative(artifact))
            elif artifact.stat().st_size != expected_size or digest(artifact) != expected_hash:
                self.error("extended_manifest", "Artifact size or SHA-256 differs", relative(artifact))
        actual = {
            artifact.relative_to(directory).as_posix()
            for artifact in directory.rglob("*")
            if artifact.is_file() and artifact.relative_to(directory).as_posix() not in omitted
        }
        for value in sorted(actual - listed):
            self.error("extended_manifest", "Unlisted artifact", "results/extended/" + value)
        for value in sorted(listed - actual):
            self.error("extended_manifest", "Listed artifact absent from inventory", "results/extended/" + value)
        self.checks["extended_manifest_integrity"] = {
            "manifest": relative(path), "entries_checked": len(entries),
            "existing_inventory_count": len(actual), "configuration_sha256_matches": configuration_matches,
            "inventory_omissions": sorted(omitted), "paths": sorted(listed),
            "scope": "Exact manifest schema, safe paths, sizes, SHA-256 and complete inventory; no solver, metric or scientific verifier execution",
        }

    def check_exports(self) -> None:
        if not self.script_imports_valid:
            raise ValueError("Exporter not loaded because documentary AST/import checks failed")
        exporter_path = ROOT / "scripts" / "export_report_material.py"
        specification = importlib.util.spec_from_file_location(
            "phase5_documentary_export", exporter_path
        )
        if specification is None or specification.loader is None:
            raise ValueError("Cannot load the documentary exporter")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        material, counts = module.build_material()
        self.material = material
        directory = ROOT / "report" / "generated"
        for name, content in material.items():
            path = directory / name
            if not path.is_file() or path.read_bytes() != content.encode("utf-8"):
                self.error("exports", "Export is missing or differs exactly from its sources", relative(path))
        actual = {path.name for path in directory.iterdir() if path.is_file()}
        for name in sorted(actual - set(material)):
            self.error("exports", "Unexpected generated file", relative(directory / name))
        self.checks["exact_documentary_exports"] = {
            "generator": relative(exporter_path), "files": sorted(material),
            "comparison": "exact UTF-8 bytes; build_material only, no writes",
            **counts,
        }
        provenance = json.loads((directory / "source_values.json").read_text("utf-8"))
        self.provenance = provenance
        if set(provenance["sources"]) != EXPECTED_SOURCES:
            self.error("provenance", "The exact seven documentary sources are not present")
        for value, expected_digest in provenance["sources"].items():
            if digest(project_path(value)) != expected_digest:
                self.error("provenance", "Source SHA-256 differs", value)
            if value not in self.baseline or self.baseline[value]["sha256"] != expected_digest:
                self.error("provenance", "Source is not bound to the protected baseline", value)
        with (ROOT / "results" / "extended" / "summary.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            summary = list(csv.DictReader(stream))
        self.summary = summary
        count = 0
        for table, entries in provenance["tables"].items():
            for entry in entries:
                index = entry["source_line"] - 2
                if entry["source_file"] != "results/extended/summary.csv" or not 0 <= index < len(summary):
                    self.error("provenance", f"Invalid source location for table {table}")
                elif entry["values"] != summary[index]:
                    self.error("provenance", f"Source values differ for table {table}, line {index + 2}")
                count += 1
        self.checks["source_value_provenance"] = {
            "path": "report/generated/source_values.json", "source_files": sorted(provenance["sources"]),
            "selected_source_rows_checked": count,
        }

    def check_documentary_texts(self) -> None:
        directories = ["report", "slides", "scripts", "docs", "references"]
        values = {"README.md"}
        for directory in directories:
            values.update(inventory(ROOT / directory, documentary=True))
        values = {
            value for value in values
            if value not in self.baseline and Path(value).suffix.lower() in DOCUMENTARY_TEXT_SUFFIXES
        }
        previous_errors = len(self.errors)
        raw_build_logs: list[str] = []
        for value in sorted(values):
            path = project_path(value)
            data = path.read_bytes()
            try:
                text = data.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exception:
                self.error("documentary_text", f"Invalid UTF-8: {exception}", value)
                continue
            if "\x00" in text:
                self.error("documentary_text", "NUL byte in text", value)
            if value.startswith(RAW_BUILD_LOG_DIRECTORY) and path.suffix.lower() == ".txt":
                # Compiler captures are documentary evidence, preserved verbatim.
                # Their whitespace and final-newline conventions are not authored prose.
                raw_build_logs.append(value)
                continue
            if not data.endswith(b"\n"):
                self.error("documentary_text", "Missing final newline", value)
            for number, line in enumerate(text.splitlines(), 1):
                if line != line.rstrip(" \t"):
                    self.error("documentary_text", f"Trailing whitespace on line {number}", value)
                if re.match(r"^(?:<{7}|={7}|>{7})(?:\s|$)", line):
                    self.error("documentary_text", f"Conflict marker on line {number}", value)
        self.checks["documentary_text_hygiene"] = {
            "scope": "README plus documentary text files in report/slides/scripts/docs/references outside protected baseline; Git tracked status is not inferred",
            "directories": directories, "suffixes": sorted(DOCUMENTARY_TEXT_SUFFIXES),
            "file_count": len(values), "paths": sorted(values),
            "raw_build_logs_utf8_and_nul_checked": raw_build_logs,
            "issues_found": len(self.errors) - previous_errors,
            "checks": ["strict UTF-8", "final newline", "trailing spaces/tabs", "conflict markers", "NUL"],
            "excluded": "Protected baseline; environments/caches/egg-info/build/dist; binary and LaTeX auxiliary files; raw compiler captures exempt only from authored-text whitespace/newline rules",
        }

    def check_negative_controls(self) -> None:
        """Four deliberately corrupted documentary examples, only in memory."""
        expected = self.material["fixed_case.tex"]
        match = re.search(r"(?<=\$)\d+\.\d+", expected)
        if match is None:
            raise ValueError("No displayed numeric cell found for the in-memory table control")
        changed_value = f"{float(match.group()) + 0.01:.4f}"
        altered = expected[:match.start()] + changed_value + expected[match.end():]
        entry = self.provenance["tables"]["fixed_case"][0]
        source = self.summary[entry["source_line"] - 2]
        altered_row = dict(entry["values"])
        altered_row["psnr_mean"] = str(float(altered_row["psnr_mean"]) + 0.01)
        brace_check = DocumentaryChecks()
        brace_check.check_tex_structure(ROOT / "report" / "main.tex", "Text with an unclosed { brace")
        environment_check = DocumentaryChecks()
        environment_check.check_tex_structure(
            ROOT / "report" / "main.tex", r"\begin{equation}x=1\end{align}"
        )
        controls = {
            "altered_generated_table_detected": altered.encode("utf-8") != expected.encode("utf-8"),
            "altered_source_value_detected": altered_row != source and entry["values"] == source,
            "unbalanced_brace_detected": any(error["check"] == "tex_braces" for error in brace_check.errors),
            "mismatched_environment_detected": any(error["check"] == "tex_environments" for error in environment_check.errors),
        }
        for name, detected in controls.items():
            if not detected:
                self.error("documentary_negative_controls", f"Corruption was not detected: {name}")
        self.checks["documentary_negative_controls"] = {
            "scope": "Four examples mutated in memory only; no file or scientific result mutation; not pytest and not part of the 165 scientific tests",
            "count": len(controls), "detected": sum(controls.values()), "controls": controls,
        }

    def check_generated_rows(self) -> None:
        rows = 0
        for path in sorted((ROOT / "report" / "generated").glob("*.tex")):
            for number, line in enumerate(clean_tex(path.read_text("utf-8")).splitlines(), 1):
                if re.search(r"(?<!\\)&", line):
                    rows += 1
                    if not line.rstrip().endswith("\\\\"):
                        self.error("table_rows", f"Table row {number} lacks a double-backslash terminator", relative(path))
        self.checks["generated_table_rows"] = rows

    def check_tex_structure(self, path: Path, text: str) -> None:
        stack: list[str] = []
        for match in re.finditer(r"\\(begin|end)\{([^\s{}]+)\}", text):
            action, name = match.groups()
            if action == "begin":
                stack.append(name)
            elif not stack or stack.pop() != name:
                self.error("tex_environments", f"Unmatched end of environment {name}", relative(path))
        if stack:
            self.error("tex_environments", f"Unclosed environments: {stack}", relative(path))
        braces = 0
        for index, character in enumerate(text):
            if character in "{}" and not escaped(text, index):
                braces += 1 if character == "{" else -1
                if braces < 0:
                    self.error("tex_braces", "Closing brace without opening brace", relative(path))
                    break
        if braces != 0:
            self.error("tex_braces", f"Unbalanced brace count: {braces}", relative(path))
        for match in PLACEHOLDERS.finditer(text):
            self.error("placeholders", f"Unresolved placeholder: {match.group()}", relative(path))

    def check_entry(self, entry: Path) -> None:
        base = entry.parent
        entry_text = clean_tex(entry.read_text("utf-8"))
        macros = dict(re.findall(r"\\(?:newcommand|renewcommand)\{\\([A-Za-z]+)\}\{([^{}]*)\}", entry_text))
        graphic_directories = [base]
        for match in re.finditer(r"\\graphicspath\s*\{\s*((?:\{[^{}]*\}\s*)+)\}", entry_text):
            graphic_directories.extend(base / value for value in re.findall(r"\{([^{}]*)\}", match.group(1)))
        documents: list[tuple[Path, str]] = []

        def visit(path: Path, ancestors: tuple[Path, ...] = ()) -> None:
            resolved = path.resolve()
            if resolved in ancestors:
                self.error("tex_inputs", "Cyclic input", relative(path))
                return
            if not resolved.is_relative_to(ROOT) or not path.is_file():
                self.error("tex_inputs", "Input is absent or outside project", str(path))
                return
            text = clean_tex(path.read_text("utf-8"))
            self.check_tex_structure(path, text)
            documents.append((path, text))
            for target in re.findall(r"\\(?:input|include)\s*\{([^{}]+)\}", text):
                child = base / target.strip()
                if not child.suffix:
                    child = child.with_suffix(".tex")
                visit(child, (*ancestors, resolved))

        visit(entry)
        labels, references, citations, bib_keys = [], [], [], []
        graphics: set[str] = set()
        bibliographies: set[str] = set()
        for path, text in documents:
            labels.extend(re.findall(r"\\label\{([^{}]+)\}", text))
            for options in re.findall(r"\\begin\{frame\}\s*\[([^\]]*)\]", text):
                labels.extend(re.findall(r"(?:^|,)\s*label\s*=\s*([^,\s]+)", options))
            references.extend(re.findall(r"\\(?:ref|eqref|pageref|autoref)\*?\{([^{}]+)\}", text))
            for group in re.findall(r"\\(?:cite[A-Za-z]*|nocite)\*?(?:\[[^\]]*\]){0,2}\{([^{}]+)\}", text):
                citations.extend(value.strip() for value in group.split(",") if value.strip() != "*")
            bib_keys.extend(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}", text))
            for group in re.findall(r"\\bibliography\{([^{}]+)\}", text):
                for value in group.split(","):
                    bibliography = base / value.strip()
                    if not bibliography.suffix:
                        bibliography = bibliography.with_suffix(".bib")
                    if not bibliography.is_file():
                        self.error("bibliography_paths", "Bibliography missing", str(bibliography))
                        continue
                    bibliographies.add(relative(bibliography))
                    bib_text = bibliography.read_text("utf-8")
                    bib_keys.extend(re.findall(r"@[A-Za-z]+\s*\{\s*([^\s,{]+)\s*,", bib_text))
            for target in re.findall(r"\\includegraphics\*?(?:\[[^\]]*\])?\s*\{([^{}]+)\}", text):
                expanded = re.sub(r"\\([A-Za-z]+)\s*", lambda match: macros.get(match.group(1), match.group()), target).strip()
                if "\\" in expanded:
                    self.error("figure_paths", f"Unresolved path macro: {target}", relative(path))
                    continue
                candidates = [directory / expanded for directory in graphic_directories]
                if not Path(expanded).suffix:
                    candidates = [candidate.with_suffix(extension) for candidate in candidates for extension in (".pdf", ".png", ".jpg")]
                found = next((candidate for candidate in candidates if candidate.is_file()), None)
                if found is None:
                    self.error("figure_paths", f"Missing figure: {target}", relative(path))
                elif not found.resolve().is_relative_to(ROOT):
                    self.error("figure_paths", "Figure outside project", str(found))
                else:
                    value = relative(found)
                    graphics.add(value)
                    if found.suffix.lower() != ".pdf":
                        self.error("figure_paths", "Document does not reuse an archived PDF", value)
                    if value not in self.baseline or digest(found) != self.baseline[value]["sha256"]:
                        self.error("figure_provenance", "Figure is not identical to protected source", value)
        for label, count in Counter(labels).items():
            if count != 1:
                self.error("tex_labels", f"Duplicate label: {label}", relative(entry))
        for value in sorted(set(references) - set(labels)):
            self.error("tex_references", f"Undefined reference: {value}", relative(entry))
        for value, count in Counter(bib_keys).items():
            if count != 1:
                self.error("citation_keys", f"Duplicate bibliography key: {value}", relative(entry))
        for value in sorted(set(citations) - set(bib_keys)):
            self.error("citations", f"Unknown cited key: {value}", relative(entry))
        self.checks[relative(entry)] = {
            "input_files": sorted({relative(path) for path, _ in documents}),
            "labels": sorted(labels), "references_checked": len(references),
            "citation_keys": sorted(set(citations)), "bibliographies": sorted(bibliographies),
            "archived_pdf_figures": sorted(graphics),
        }

    def check_notes_and_figures(self) -> None:
        slides = clean_tex((ROOT / "slides" / "main.tex").read_text("utf-8"))
        appendix = slides.find("\\appendix")
        frames: list[tuple[str, bool]] = []
        for match in re.finditer(r"\\begin\{frame\}\s*\[([^\]]*)\]", slides):
            labels = re.findall(r"(?:^|,)\s*label\s*=\s*([^,\s]+)", match.group(1))
            if len(labels) != 1:
                self.error("speaker_notes", "Each frame needs exactly one label")
                continue
            frames.append((labels[0], appendix >= 0 and match.start() > appendix))
        total_frames = len(re.findall(r"\\begin\{frame\}", slides))
        if total_frames != len(frames):
            self.error("speaker_notes", "Some frames lack labels")
        main_count = sum(not reserve for _, reserve in frames)
        reserve_count = sum(reserve for _, reserve in frames)
        if (main_count, reserve_count) != (25, 7):
            self.error("speaker_notes", f"Expected 25 main and 7 reserve frames; got {main_count}, {reserve_count}")
        notes_path = ROOT / "slides" / "speaker_notes.md"
        notes = notes_path.read_text("utf-8")
        headers = re.findall(r"^##\s+(?:\d+\.\s+|Réserve\s+\d+\.\s+).*?\(([^()]+)\).*?$", notes, re.MULTILINE)
        if headers != [label for label, _ in frames]:
            self.error("speaker_notes", "Notes do not cover frame labels once in presentation order", relative(notes_path))
        for label, count in Counter(label for label, _ in frames).items():
            if count != 1:
                self.error("speaker_notes", f"Frame label is not unique: {label}")
        for label, count in Counter(headers).items():
            if count != 1:
                self.error("speaker_notes", f"Note header label is not unique: {label}", relative(notes_path))
        for match in PLACEHOLDERS.finditer(notes):
            self.error("placeholders", f"Unresolved placeholder: {match.group()}", relative(notes_path))
        duration = sum(float(value.replace(",", ".")) for value in re.findall(
            r"^##\s+\d+\..*?—\s*(\d+(?:[.,]\d+)?)\s*minute", notes, re.MULTILINE
        ))
        if abs(duration - 23.0) > 0.5:
            self.error("speaker_notes", f"Main talk duration must stay within 23 +/- 0.5 min; got {duration}", relative(notes_path))
        self.checks["speaker_notes"] = {
            "path": relative(notes_path), "main_frames": main_count,
            "reserve_frames": reserve_count, "covered_labels": headers,
            "main_duration_minutes_indicative": duration,
            "required_main_duration_minutes_indicative": [22.5, 23.5],
        }
        pdfs = sorted((ROOT / "results" / "extended" / "figures").glob("*.pdf"))
        for path in pdfs:
            content = path.read_bytes()
            if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-1024:]:
                self.error("pdf_headers", "Invalid basic PDF header/end marker", relative(path))
            value = relative(path)
            if value not in self.baseline or digest(path) != self.baseline[value]["sha256"]:
                self.error("figure_provenance", "Archived PDF differs from the baseline", value)
        if not pdfs:
            self.error("pdf_headers", "No archived figure PDF found")
        self.checks["available_archived_figure_pdfs"] = [relative(path) for path in pdfs]

    def run(self) -> dict[str, Any]:
        self.run_check("script_ast", self.check_scripts)
        self.run_check("protection", self.check_protection)
        self.run_check("extended_manifest", self.check_extended_manifest)
        self.run_check("exports", self.check_exports)
        self.run_check("documentary_text", self.check_documentary_texts)
        self.run_check("documentary_negative_controls", self.check_negative_controls)
        self.run_check("table_rows", self.check_generated_rows)
        for entry in (ROOT / "report" / "main.tex", ROOT / "slides" / "main.tex"):
            self.run_check("latex_entry", lambda path=entry: self.check_entry(path))
        self.run_check("notes_and_figures", self.check_notes_and_figures)
        return {
            "status": "passed" if not self.errors else "failed",
            "scope": "phase5 static documentary checks; read-only unless --report",
            "scientific_imports_or_experiments": False,
            "checks": self.checks, "errors": self.errors,
            "latex_tools_detected": {
                "on_path": {tool: shutil.which(tool) for tool in ("pdflatex", "latexmk", "bibtex", "kpsewhich", "tectonic")},
                "authorized_portable_tectonic_files": [
                    str(path) for path in sorted((ROOT.parent / "_tools" / "tectonic").glob("*/tectonic.exe"))
                    if path.is_file()
                ],
                "scope": "PATH/file existence detection only; executable launch and LaTeX compilation are not tested by this script",
            },
            "limitations": [
                "Static brace/environment/path checks are not a complete TeX parser or compilation.",
                "Report and slides compilation, pagination, resolved bibliographic output, overflows and rendered layout are not validated by this script.",
                "Archived PDF figures receive exact provenance and basic header/end-marker checks, not a PDF rendering inspection by this script.",
                "Citation keys are checked locally; primary-source access and scientific claims require the source ledger and human review.",
                "The scientific test suite, solvers, metrics, runner and experimental verifier are not imported or executed.",
            ],
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", nargs="?", const="docs/phase5_documentary_checks.json",
        help="Also write only docs/phase5_documentary_checks.json or docs/phase5_v2_documentary_checks.json",
    )
    arguments = parser.parse_args()
    if arguments.report is not None:
        requested = Path(arguments.report)
        if not requested.is_absolute():
            requested = ROOT / requested
        if requested.resolve() not in ALLOWED_REPORT_DESTINATIONS:
            parser.error("--report permits only the phase5 or phase5_v2 documentary report path")
    payload = DocumentaryChecks().run()
    if arguments.report is not None:
        destination = requested.resolve()
        payload["written_report"] = relative(destination)
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
