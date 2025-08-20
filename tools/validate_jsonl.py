#!/usr/bin/env python3
import argparse
import glob
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

import jsonschema


def fill_templates(s: str) -> str:
    """Fill {date_str} and {hour_str} using env or current UTC."""
    now = datetime.now(timezone.utc)
    date_str = os.environ.get("DATE_STR", now.strftime("%Y-%m-%d"))
    hour_str = os.environ.get("HOUR_STR", now.strftime("%H"))
    return s.replace("{date_str}", date_str).replace("{hour_str}", hour_str)


def validate_file(schema, input_file):
    """Validate one JSONL file against schema"""
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
    parser = argparse.ArgumentParser(description="Validate JSONL file(s) against JSON schema (glob + templates supported)")
    parser.add_argument("--schema", required=True, help="Path to schema JSON file")
    parser.add_argument("--input", required=True, help="Path, template, or glob to JSONL file(s)")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    if not schema_path.exists():
        sys.exit(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # NEW: fill {date_str} and {hour_str} from env (fallback to UTC now)
    pattern = fill_templates(args.input)

    # Support globs (including after templates are filled)
    files = glob.glob(pattern)
    if not files:
        sys.exit(f"No files matched pattern: {args.input} -> {pattern}")

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
        print(f"All {len(files)} file(s) passed schema validation.")


if __name__ == "__main__":
    main()
