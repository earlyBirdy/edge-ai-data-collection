#!/usr/bin/env python3
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Optional dependency: jsonschema
try:
    import jsonschema  # type: ignore
    HAS_JSONSCHEMA = True
except Exception:
    HAS_JSONSCHEMA = False


def fill_templates(s: str) -> str:
    """Fill {date_str} and {hour_str} placeholders from env or current UTC."""
    now = datetime.now(timezone.utc)
    date_str = os.environ.get("DATE_STR", now.strftime("%Y-%m-%d"))
    hour_str = os.environ.get("HOUR_STR", now.strftime("%H"))
    # Support both str.format and literal replacement
    try:
        return s.format(date_str=date_str, hour_str=hour_str)
    except Exception:
        return s.replace("{date_str}", date_str).replace("{hour_str}", hour_str)


def broaden_to_date_glob(filled_pattern: str) -> str:
    """Broaden a specific hour file pattern to its date directory, e.g. temperature-*.jsonl"""
    p = Path(filled_pattern)
    parent = p.parent
    stem = p.stem  # e.g. temperature-2025-08-19T04-00
    if "T" in stem:
        prefix = stem.split("T")[0]  # temperature-YYYY-MM-DD
        return str(parent / f"{prefix}T*.jsonl")
    return str(parent / "temperature-*.jsonl")


def widen_to_all_dates_glob(filled_pattern: str) -> str:
    """Broaden search across all date partitions: */temperature-*.jsonl two dirs up."""
    p = Path(filled_pattern)
    try:
        return str(p.parent.parent / "*/temperature-*.jsonl")
    except Exception:
        return str(p)


def find_latest(files):
    """Return a single most-recently modified file from a list."""
    files = [str(f) for f in files]
    if not files:
        return None
    files = sorted(set(files), key=lambda f: Path(f).stat().st_mtime, reverse=True)
    return files[0]


def is_iso8601(s: str) -> bool:
    try:
        if s.endswith("Z"):
            datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            datetime.fromisoformat(s)
        return True
    except Exception:
        return False


def validate_one_object(obj, schema):
    """Lightweight checks if jsonschema isn't available."""
    errors = []

    required = set(schema.get("required", []))
    props = schema.get("properties", {})

    missing = required - set(obj.keys())
    if missing:
        errors.append(f"missing required fields: {sorted(missing)}")
        return errors

    for key, spec in props.items():
        if key not in obj:
            continue
        v = obj[key]
        t = spec.get("type")
        if t == "string" and not isinstance(v, str):
            errors.append(f"{key} must be string")
        elif t == "number" and not isinstance(v, (int, float)):
            errors.append(f"{key} must be number")
        elif t == "integer" and not isinstance(v, int):
            errors.append(f"{key} must be integer")
        if spec.get("format") == "date-time":
            if not isinstance(v, str) or not is_iso8601(v):
                errors.append(f"{key} must be ISO8601 date-time")
        if "enum" in spec and v not in spec["enum"]:
            errors.append(f"{key} must be one of {spec['enum']}")
    return errors


def validate_file(schema, path):
    errs = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            ln = line.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
                if HAS_JSONSCHEMA:
                    jsonschema.validate(instance=obj, schema=schema)  # type: ignore
                else:
                    for e in validate_one_object(obj, schema):
                        errs.append(f"{path}:{i}: {e}")
            except json.JSONDecodeError as e:
                errs.append(f"{path}:{i}: invalid JSON ({e})")
            except Exception as e:
                errs.append(f"{path}:{i}: schema validation error ({e})")
    return errs


def collect_files(pattern: str, strict: bool):
    """Resolve files; auto-fallback to latest if strict=False."""
    # Exact/glob first
    files = glob.glob(pattern)
    if files:
        return sorted(set(files))

    # Broaden within same date dir
    date_glob = broaden_to_date_glob(pattern)
    files = glob.glob(date_glob)
    if files:
        return sorted(set(files))

    if strict:
        return []

    # Auto-fallback: latest within same date dir
    latest = find_latest(files)
    if latest:
        return [latest]

    # Still none: widen to all dates and pick latest
    all_dates = glob.glob(widen_to_all_dates_glob(pattern))
    latest = find_latest(all_dates)
    return [latest] if latest else []


def main():
    ap = argparse.ArgumentParser(description="Validate JSONL against JSON schema (templates, globs, auto-latest fallback).")
    ap.add_argument("--schema", required=True, help="Path to schema JSON file")
    ap.add_argument("--input", required=True, help="Path/Glob with optional {date_str}/{hour_str}")
    ap.add_argument("--strict", action="store_true", help="Disable auto-latest fallback (fail if no match)")
    args = ap.parse_args()

    # Load schema
    with open(args.schema, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Fill templates
    filled = fill_templates(args.input)

    # Resolve files (with/without fallback)
    files = collect_files(filled, strict=args.strict)
    if not files:
        print(f"No files matched pattern: {args.input} -> {filled}", file=sys.stderr)
        sys.exit(1)

    all_errs = []
    for fp in files:
        all_errs.extend(validate_file(schema, fp))

    if all_errs:
        for e in all_errs:
            print(e, file=sys.stderr)
        sys.exit(2)
    else:
        if len(files) == 1:
            print(f"OK: {files[0]}")
        else:
            print(f"OK: {len(files)} files validated")


if __name__ == "__main__":
    main()
