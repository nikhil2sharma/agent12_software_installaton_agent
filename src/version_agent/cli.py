"""Command-line entry point: read a CSV, look up versions, write a report."""

import argparse
import csv
import logging
import os
import sys
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

from .checker import DEFAULT_MODEL, compare, find_latest_version

log = logging.getLogger("version_agent")

REQUIRED_COLUMNS = {"name"}


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing column(s): {', '.join(sorted(missing))}")
        return [row for row in reader if row.get("name", "").strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def check_all(client: Any, rows: list[dict], model: str) -> list[dict]:
    for row in rows:
        name = row["name"].strip()
        current = (row.get("version") or "").strip()
        latest = find_latest_version(client, name, (row.get("url") or "").strip(), model)
        row["latest_version"] = latest
        row["status"] = compare(current, latest)
        print(f"{name:<20} {current or '-':<12} -> {latest:<12} [{row['status']}]", flush=True)
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="version-agent",
        description="Check software versions against the latest stable release.",
    )
    parser.add_argument("input", type=Path, help="CSV with columns: name, version (opt), url (opt)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("latest_versions.csv"),
        help="report path (default: %(default)s)",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help="Claude model (default: %(default)s)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    try:
        rows = read_rows(args.input)
    except (OSError, ValueError) as exc:
        log.error("Could not read input: %s", exc)
        return 1
    if not rows:
        log.error("No rows to check in %s", args.input)
        return 1

    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.error("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.")
        return 2
    client = anthropic.Anthropic()

    write_rows(args.output, check_all(client, rows, args.model))
    print(f"\nReport written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
