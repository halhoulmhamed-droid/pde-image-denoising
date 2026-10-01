"""Command-line entry point for the authorised quick and extended experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .experiments import load_config, run_and_write


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a quick or extended JSON file")
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    config_path = Path(arguments.config).resolve()
    config = load_config(config_path)
    output_dir = Path(config["output_dir"])
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir
    outcome = run_and_write(config, output_dir)
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    main()
