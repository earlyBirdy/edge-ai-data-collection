import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
try:
    from adapters.writer import write_jsonl
except Exception:
    # allow running as a script from repo root (PYTHONPATH not set)
    import os
    sys.path.append(os.getcwd())
    from adapters.writer import write_jsonl  # type: ignore

def main():
    ap = argparse.ArgumentParser(description="Base adapter")
    ap.add_argument("--output", required=True, help="Output JSONL file")
    ap.add_argument("--limit", type=int, default=10, help="Max records to capture (0 = infinite)")
    ap.add_argument("--config", help="Adapter-specific JSON config (inline or @path.json)")
    args = ap.parse_args()

    cfg = {}
    if args.config:
        if args.config.startswith("@"):
            _cfg = json.loads(Path(args.config[1:]).read_text(encoding="utf-8"))
        else:
            _cfg = json.loads(args.config)

    def gen():
        # placeholder generator; overridden in specific adapters
        yield {"source": "base", "message": "adapter stub", "ts": datetime.now(timezone.utc).isoformat()}

    write_jsonl(args.output, gen())

if __name__ == "__main__":
    main()
