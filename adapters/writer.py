from pathlib import Path
import json
import time
from datetime import datetime, timezone
try:
    from common.logger import get_logger
except Exception:
    import os, sys
    sys.path.append(os.getcwd())
    from common.logger import get_logger  # type: ignore

logger = get_logger(__name__)


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