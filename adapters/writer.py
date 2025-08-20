from pathlib import Path
import json
import time
from datetime import datetime, timezone

def write_jsonl(output_path, records_iter):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        for rec in records_iter:
            if "ts" not in rec:
                rec["ts"] = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            time.sleep(0.0)
