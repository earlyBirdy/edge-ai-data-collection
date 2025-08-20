#!/usr/bin/env python3
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema


def fill_templates(s: str) -> str:
    \"\"\"Fill {date_str} and {hour_str} placeholders from env or current UTC.\"\"\"
    now = datetime.now(timezone.utc)
    date_str = os.environ.get("DATE_STR", now.strftime("%Y-%m-%d"))
    hour_str = os.environ.get("HOUR_STR", now.strftime("%H"))
    return s.replace("{date_str}", date_str).replace("{hour_str}", hour_str)


def broaden_to_date_glob(filled_pattern: str) -> str:
    \"\"\"
    If pattern points to a single hour file like
    .../YYYY-MM-DD/temperature-YYYY-MM-DDTHH-00.jsonl,
    broaden it to the date directory with filename wildcard:
    .../YYYY-MM-DD/temperature-*.jsonl
    \"\"\"
    p = Path(filled_pattern)
    try:
        parent = p.parent
        return str(parent / "temperature-*.jsonl")
    except Exception:
        return filled_pattern


def find_latest(files):
    \"\"\"Pick the most recently modified file from a list (mtime).\"\"\"
    if not files:
        return []
    files = list({str(f) for f in files})
    files.sort(key=lambda x: Path(x).stat().st_mtime)
    return [files[-1]]


def validate_file(schema, input_file):
    \"\"\"Validate one JSONL file against schema; return list of error strings.\"\"\"
    errors = []
    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                jsonschema.validate(instance=obj, schema=schema)
            except json.JSONDecodeError as e:
                errors.append(f"{input_file} line {i}: invalid JSON ({e})")
            except jsonschema.ValidationError as e:
                errors.append(f"{input_file} line {i}: schema validation error ({e.message})")
    return errors


def main():
    ap = argparse.ArgumentParser(description="Validate JSONL file(s) against JSON schema (templates, globs, and --latest supported)")
    ap.add_argument("--schema", required=True, help="Path to schema JSON file")
    ap.add_argument("--input", required=True, help="Path/Glob, optionally with {date_str}/{hour_str} templates")
    ap.add_argument("--latest", action="store_true", help="If no exact match, pick the most recent file for that date; if still none, pick most recent overall match")
    args = ap.parse_args()

    schema_path = Path(args.schema)
    if not schema_path.exists():
        sys.exit(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Fill templates from env (UTC fallback)
    filled = fill_templates(args.input)

    # First pass: exact/glob as provided (after fill)
    files = glob.glob(filled)

    # If nothing found and --latest requested, try to broaden within the same date directory
    if not files and args.latest:
        date_glob = broaden_to_date_glob(filled)
        date_matches = glob.glob(date_glob)
        if date_matches:
            files = find_latest(date_matches)

    # If still nothing and --latest, broaden one more level: parent of date directory
    if not files and args.latest:
        p = Path(filled)
        wide_glob = str(p.parent.parent / "*/temperature-*.jsonl")
        wide_matches = glob.glob(wide_glob)
        if wide_matches:
            files = find_latest(wide_matches)

    if not files:
        sys.exit(f"No files matched pattern: {args.input} -> {filled}"
                 + (" (no broader matches found with --latest)" if args.latest else ""))

    all_errors = []
    for fpath in files:
        errs = validate_file(schema, fpath)
        if errs:
            all_errors.extend(errs)

    if all_errors:
        print("Validation failed with errors:")
        for e in all_errors:
            print(" -", e)
        sys.exit(1)
    else:
        if len(files) == 1:
            print(f"OK: {files[0]} passed schema validation.")
        else:
            print(f"OK: All {len(files)} files passed schema validation.")


if __name__ == "__main__":
    main()
