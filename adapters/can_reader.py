import argparse
import sys
from datetime import datetime, timezone
try:
    import can  # python-can
    HAS_CAN = True
except Exception:
    HAS_CAN = False

try:
    from adapters.writer import write_jsonl
except Exception:
    import os
    sys.path.append(os.getcwd())
    from adapters.writer import write_jsonl  # type: ignore

def main():
    ap = argparse.ArgumentParser(description="CAN bus reader → JSONL")
    ap.add_argument("--channel", default="can0")
    ap.add_argument("--bustype", default="socketcan")  # linux
    ap.add_argument("--bitrate", type=int, default=500000)
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not HAS_CAN:
        print("python-can not installed. pip install python-can", file=sys.stderr)
        sys.exit(2)

    bus = can.interface.Bus(channel=args.channel, bustype=args.bustype, bitrate=args.bitrate)

    def gen():
        count = 0
        for msg in bus:
            rec = {
                "source": "CAN",
                "device": args.channel,
                "arbitration_id": msg.arbitration_id,
                "dlc": msg.dlc,
                "data_hex": msg.data.hex(),
                "ts": datetime.now(timezone.utc).isoformat()
            }
            yield rec
            count += 1
            if args.limit and count >= args.limit:
                break

    write_jsonl(args.output, gen())

if __name__ == "__main__":
    main()
