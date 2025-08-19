# src/batcher.py
import pathlib
import json
import datetime
import re
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

# Matches telemetry.YYYY-MM-DD.jsonl
PATTERN = re.compile(r"^(?P<prefix>\w+)\.(?P<date>\d{4}-\d{2}-\d{2})\.jsonl$")

def _iter_jsonl(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                yield json.loads(s)
            except Exception:
                continue

def _ts_to_parts(ts_iso: str):
    try:
        dt = datetime.datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    except Exception:
        dt = datetime.datetime.utcnow()
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H")

def run_batcher(config_path: str):
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    hot_dir = pathlib.Path(cfg["storage"]["hot_dir"])
    batches_dir = pathlib.Path(cfg["storage"]["batches_dir"])
    batches_dir.mkdir(parents=True, exist_ok=True)

    files = list(hot_dir.glob("*.jsonl"))
    if not files:
        print("[batcher] no JSONL files found in", hot_dir)
        return

    for jfile in files:
        m = PATTERN.match(jfile.name)
        if not m:
            continue

        print("[batcher] processing", jfile.name)
        buckets = {}
        for rec in _iter_jsonl(jfile):
            ts = rec.get("ts")
            d, h = _ts_to_parts(ts) if ts else (m.group("date"), "00")
            buckets.setdefault((d, h), []).append(rec)

        for (d, h), rows in buckets.items():
            df = pd.DataFrame(rows)
            part_dir = batches_dir / f"date={d}" / f"hour={h}"
            part_dir.mkdir(parents=True, exist_ok=True)
            out = part_dir / (jfile.stem + ".parquet")
            table = pa.Table.from_pandas(df, preserve_index=False)
            pq.write_table(table, out)
            print("[batcher] wrote", out)
