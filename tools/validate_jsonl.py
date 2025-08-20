#!/usr/bin/env python3
import argparse
import glob
import json
import sys
from pathlib import Path

import jsonschema


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
    parser = argparse.ArgumentParser(description="Validate JSONL file(s) against JSON schema")
    parser.add_argument("--schema", required=True, help="Path to schema JSON file")
    parser.add_argument("--input", required=True, help="Path or glob to JSONL file(s)")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    if not schema_path.exists():
        sys.exit(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    files = glob.glob(args.input)
    if not files:
        sys.exit(f"No files matched pattern: {args.input}")

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
