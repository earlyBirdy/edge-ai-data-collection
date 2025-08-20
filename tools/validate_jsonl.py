#!/usr/bin/env python3
import argparse
import json
import os
import sys
import glob
from datetime import datetime, timezone
from pathlib import Path

import jsonschema


def fill_templates(s: str) -> str:
    """Fill {date_str} and {hour_str} placeholders from env or current UTC."""
    now = datetime.now(timezone.utc)
    date_str = os.environ.get("DATE_STR", now.strftime("%Y-%m-%d"))
    hour_str = os.environ.get("HOUR_STR", now.strftime("%H"))
    return s.format(date_str=date_str, hour_str=hour_str)


def broaden_to_date_glob(filled_pattern: str) -> str:
    """
    If pattern points to a single hour file like
    .../YYYY-MM-DD/temperature-YYYY-MM-DDTHH-00.jsonl,
    broaden it to the date directory with filename wildcard:
    .../YYYY-MM-DD/temperature-*.jsonl
    """
    p = Path(filled_pattern)
    try:
        parent = p.parent
        stem = p.stem.split("T")[0]  # e.g. temperature-2025-08-19
        return str(parent / f"{stem}T*.jsonl")
    except Exception:
        return filled_pattern


def find_latest(files):
    """Pick the most recently modified file from a list (mtime)."""
    if not files:
        return None
    files = list({str(f) for f in files})
    files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
    return files[0]


def validate_file(schema, input_file):
    """Validate one JSONL file against schema; return list of error strings."""
    errors = []
    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                jsonschema.validate(instance=obj, schema=schema)
            except Exception as e:
                errors.append(f"{input_file}:{i}: {e}")
    return errors


def main():
    ap = argparse.ArgumentParser(
        description="Validate JSONL file(s) against JSON schema "
                    "(templates + glob + auto-latest supported)"
    )
    ap.add_argument("--schema", required=True, help="Path to schema JSON file")
    ap.add_argument("--input", required=True, help="Path pattern for input JSONL(s)")
    ap.add_argument(
        "--no-latest", action="store_true",
        help="Disable automatic fallback to latest file if no match found"
    )
    args = ap.parse_args()

    # load schema
    with open(args.schema, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # fill templates
    filled_pattern = fill_templates(args.input)
    files = glob.glob(filled_pattern)

    if not files:
        # try broadening to wildcard
        broadened = broaden_to_date_glob(filled_pattern)
        files = glob.glob(broadened)

    if not files and not args.no_latest:
        # fallback: find latest file under same date dir
        broadened = broaden_to_date_glob(filled_pattern)
        candidates = glob.glob(broadened)
        latest = find_latest(candidates)
        if latest:
            print(f"[info] No exact match, falling back to latest: {latest}", file=sys.stderr)
            files = [latest]

    if not files:
        print(f"No files matched pattern: {args.input} -> {filled_pattern}", file=sys.stderr)
        sys.exit(1)

    all_errors = []
    for fpath in files:
        all_errors.extend(validate_file(schema, fpath))

    if all_errors:
        for e in all_errors:
            print(e, file=sys.stderr)
        sys.exit(2)
    else:
        print(f"Validated {len(files)} file(s): OK")


if __name__ == "__main__":
    main()
