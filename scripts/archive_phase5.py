"""Create and read-only verify the phase-5 documentary audit ZIP.

Uses only the Python standard library. It never imports project code,
launches calculations, or writes inside the project. Run after documentary
checks have finished, so the archived inputs remain stable.
The default preserves the original archive edition. --name phase5-v2
requires report/main.pdf and slides/main.pdf before any ZIP is created.
--name phase5-v2-sources exports uncompiled sources for external compilation
without weakening the compiled-document edition's requirements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import zipfile


EXPECTED_ROOT = Path(r"D:\academic-projects\pde-image-denoising")
ARCHIVE_BASENAME = "pde-image-denoising-audit-phase5"
ARCHIVE_NAMES = {
    "phase5": ARCHIVE_BASENAME,
    "phase5-v2": ARCHIVE_BASENAME + "-v2",
    "phase5-v2-sources": ARCHIVE_BASENAME + "-v2-sources",
}
COMPILED_DOCUMENTS = ("report/main.pdf", "slides/main.pdf")
SOURCES_REQUIRED_FILES = (
    "report/main.tex",
    "report/references.bib",
    "report/generated/source_values.json",
    "slides/main.tex",
    "slides/speaker_notes.md",
    "references/source_ledger.md",
    "configs/extended.json",
    "docs/phase5_protection_before.json",
    "docs/phase5_protection_after.json",
    "docs/phase5_v2_protection_check.json",
    "docs/phase5_v2_documentary_checks.json",
    "docs/phase5_v2_build/compiler.json",
    "docs/phase5_v2_build/launch_failure.txt",
    "docs/phase5_v2_sources_export.md",
)
WHOLE_DIRECTORIES = (
    "report",
    "slides",
    "scripts",
    "docs",
    "references",
    "configs",
    "results/extended/tables",
    "results/extended/figures",
)
REQUIRED_FILES = (
    "README.md",
    "results/extended/metrics.csv",
    "results/extended/summary.csv",
    "results/extended/config_used.json",
    "results/extended/environment.json",
    "results/extended/analysis.json",
    "results/extended/verification.json",
    "results/extended/manifest.json",
    "results/extended/run.log",
)
EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".cache",
        ".ipynb_checkpoints",
        "build",
        "dist",
    }
)
EXCLUDED_FILENAMES = frozenset({".ds_store", "thumbs.db", "desktop.ini"})
EXCLUDED_SUFFIXES = (
    ".exe",
    ".dll",
    ".pyd",
    ".pyc",
    ".pyo",
    ".npz",
    ".tmp",
    ".temp",
    ".bak",
    ".swp",
    ".swo",
    ".aux",
    ".bbl",
    ".blg",
    ".out",
    ".toc",
    ".lof",
    ".lot",
    ".nav",
    ".snm",
    ".vrb",
    ".fls",
    ".fdb_latexmk",
    ".synctex.gz",
    ".dvi",
    ".xdv",
)
EXCLUDED_PATH_PREFIXES = ("docs/phase5_v2_build/previews/",)


def _json(value: dict[str, object]) -> None:
    print(json.dumps(value, ensure_ascii=True, indent=2, allow_nan=False))


def _assert_regular_location(path: Path, root: Path) -> None:
    """Reject links/reparse points at every component inside the source."""
    try:
        relative = path.absolute().relative_to(root.absolute())
    except ValueError as error:
        raise ValueError(f"Path is outside the project: {path}") from error
    current = root
    components = (root, *(root.joinpath(*relative.parts[:n])
                          for n in range(1, len(relative.parts) + 1)))
    for current in components:
        metadata = current.lstat()
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        attributes = getattr(metadata, "st_file_attributes", 0)
        if stat.S_ISLNK(metadata.st_mode) or attributes & reparse_flag:
            raise ValueError(f"Symlink or junction/reparse point rejected: {current}")
    if not path.resolve(strict=True).is_relative_to(root.resolve(strict=True)):
        raise ValueError(f"Resolved path is outside the project: {path}")


def _valid_relative_name(name: str) -> bool:
    candidate = PurePosixPath(name)
    return (
        bool(name)
        and "\\" not in name
        and ":" not in name
        and not candidate.is_absolute()
        and not PureWindowsPath(name).drive
        and not PureWindowsPath(name).root
        and all(component not in {"", ".", ".."} for component in name.split("/"))
        and candidate.as_posix() == name
    )


def _excluded(name: str) -> bool:
    candidate = PurePosixPath(name)
    parts = tuple(part.casefold() for part in candidate.parts)
    basename = parts[-1]
    return (
        any(name.casefold().startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES)
        or any(part in EXCLUDED_DIRECTORIES or part.endswith(".egg-info")
            for part in parts[:-1])
        or basename in EXCLUDED_FILENAMES
        or basename.startswith("~$")
        or basename.endswith("~")
        or basename.endswith(EXCLUDED_SUFFIXES)
        or (basename.endswith(".log") and basename != "run.log")
    )


def _collect_files(root: Path, *, require_compiled_pdf: bool = False) -> list[Path]:
    def fail_on_walk_error(error: OSError) -> None:
        raise error

    required = REQUIRED_FILES + (COMPILED_DOCUMENTS if require_compiled_pdf else ())
    missing = [name for name in required if not (root / name).is_file()]
    missing.extend(
        name for name in WHOLE_DIRECTORIES if not (root / name).is_dir()
    )
    if missing:
        raise FileNotFoundError(f"Missing required archive inputs: {missing}")
    files = {root / name for name in required}
    for directory in WHOLE_DIRECTORIES:
        top = root / directory
        _assert_regular_location(top, root)
        for current_name, directory_names, file_names in os.walk(
            top, topdown=True, followlinks=False, onerror=fail_on_walk_error
        ):
            current = Path(current_name)
            retained_directories: list[str] = []
            for name in sorted(directory_names):
                if name.casefold() in EXCLUDED_DIRECTORIES:
                    continue
                if name.casefold().endswith(".egg-info"):
                    continue
                path = current / name
                if any((path.relative_to(root).as_posix() + "/").casefold().startswith(prefix)
                       for prefix in EXCLUDED_PATH_PREFIXES):
                    continue
                _assert_regular_location(path, root)
                retained_directories.append(name)
            directory_names[:] = retained_directories
            for name in sorted(file_names):
                path = current / name
                relative = path.relative_to(root).as_posix()
                if _excluded(relative):
                    continue
                _assert_regular_location(path, root)
                if not path.is_file():
                    raise ValueError(f"Archive input is not a regular file: {path}")
                files.add(path)
    selected = sorted(files, key=lambda path: path.relative_to(root).as_posix())
    for path in selected:
        _assert_regular_location(path, root)
        relative = path.relative_to(root).as_posix()
        if not _valid_relative_name(relative) or _excluded(relative):
            raise ValueError(f"Invalid or excluded archive input: {relative}")
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"Archive input is not a regular file: {path}")
    return selected


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot(root: Path, files: list[Path]) -> dict[str, dict[str, object]]:
    inventory: dict[str, dict[str, object]] = {}
    for path in files:
        _assert_regular_location(path, root)
        before = path.stat()
        fingerprint = _sha256_file(path)
        after = path.stat()
        before_signature = (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns
        )
        after_signature = (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        )
        if before_signature != after_signature:
            raise RuntimeError(f"Source changed while fingerprinting: {path}")
        inventory[path.relative_to(root).as_posix()] = {
            "sha256": fingerprint,
            "size_bytes": after.st_size,
        }
    return inventory


def _create_archive(
    root: Path, inventory: dict[str, dict[str, object]], basename: str = ARCHIVE_BASENAME
) -> Path:
    suffix = 0
    while True:
        stem = basename if suffix == 0 else f"{basename}-{suffix}"
        destination = root.parent / f"{stem}.zip"
        if destination.exists():
            suffix += 1
            continue
        try:
            archive = zipfile.ZipFile(
                destination,
                mode="x",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=6,
                strict_timestamps=False,
            )
        except FileExistsError:
            suffix += 1
            continue
        with archive:
            for name in inventory:
                path = root / name
                _assert_regular_location(path, root)
                archive.write(path, arcname=name)
        return destination


def _verify_archive(
    root: Path, destination: Path, inventory: dict[str, dict[str, object]],
    *, require_compiled_pdf: bool = False,
) -> None:
    with zipfile.ZipFile(destination, mode="r") as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise RuntimeError("ZIP contains duplicate entries")
        invalid = [
            name for name in names
            if not _valid_relative_name(name) or _excluded(name)
        ]
        if invalid:
            raise RuntimeError(f"ZIP contains invalid/excluded entries: {invalid}")
        if set(names) != set(inventory):
            raise RuntimeError("ZIP inventory differs from the source inventory")
        corrupt_entry = archive.testzip()
        if corrupt_entry is not None:
            raise RuntimeError(f"ZIP CRC integrity failure: {corrupt_entry}")
        for entry in entries:
            if entry.is_dir():
                raise RuntimeError(f"Unexpected directory entry: {entry.filename}")
            source_metadata = inventory[entry.filename]
            if entry.file_size != source_metadata["size_bytes"]:
                raise RuntimeError(f"ZIP size mismatch: {entry.filename}")
            digest = hashlib.sha256()
            with archive.open(entry, mode="r") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != source_metadata["sha256"]:
                raise RuntimeError(f"ZIP SHA-256 mismatch: {entry.filename}")
    after_files = _collect_files(root, require_compiled_pdf=require_compiled_pdf)
    if set(path.relative_to(root).as_posix() for path in after_files) != set(inventory):
        raise RuntimeError("Project inventory changed during archive creation")
    if _snapshot(root, after_files) != inventory:
        raise RuntimeError("Project file contents changed during archive creation")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--name", choices=tuple(ARCHIVE_NAMES), default="phase5",
        help="Audit edition: phase5-v2 requires both compiled PDFs; phase5-v2-sources permits uncompiled sources",
    )
    arguments = parser.parse_args()
    require_compiled_pdf = arguments.name == "phase5-v2"
    destination: Path | None = None
    try:
        script_path = Path(__file__).absolute()
        root = script_path.parents[1]
        if root != EXPECTED_ROOT:
            raise ValueError(f"Unexpected project root: {root}")
        _assert_regular_location(script_path, root)
        if arguments.name == "phase5-v2-sources":
            missing_sources = [
                name for name in SOURCES_REQUIRED_FILES if not (root / name).is_file()
            ]
            if missing_sources:
                raise FileNotFoundError(
                    f"Missing required source-edition inputs: {missing_sources}"
                )
        files = _collect_files(root, require_compiled_pdf=require_compiled_pdf)
        inventory = _snapshot(root, files)
        destination = _create_archive(root, inventory, ARCHIVE_NAMES[arguments.name])
        _verify_archive(root, destination, inventory, require_compiled_pdf=require_compiled_pdf)
        size = destination.stat().st_size
        _json(
            {
                "status": "passed",
                "archive_edition": arguments.name,
                "archive_path": str(destination),
                "size_bytes": size,
                "size_mib": round(size / (1024 * 1024), 6),
                "file_count": len(inventory),
                "archive_sha256": _sha256_file(destination),
                "crc_integrity": "passed",
                "exact_inventory": True,
                "entry_sha256_matches_source": True,
                "project_unchanged_during_archive": True,
                "invalid_entries": [],
                "missing_required": [],
                "compiled_documents_required": require_compiled_pdf,
                "uncompiled_source_edition": arguments.name == "phase5-v2-sources",
                "source_edition_notice": (
                    "Uncompiled sources; rendering of 25 main frames and 7 backup frames remains to be verified."
                    if arguments.name == "phase5-v2-sources" else None
                ),
                "omitted": ["NPZ arrays", "environments/executables/caches", "LaTeX auxiliary files", *EXCLUDED_PATH_PREFIXES],
            }
        )
        return 0
    except Exception as error:
        _json(
            {
                "status": "failed",
                "archive_path": None if destination is None else str(destination),
                "error_type": type(error).__name__,
                "error": str(error),
                "note": "No source file was written. Any partial ZIP is retained.",
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
