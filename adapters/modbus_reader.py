import argparse
import sys
from datetime import datetime, timezone
try:
    from common.logger import get_logger
except Exception:
import os
import sys
    sys.path.append(os.getcwd())
    from common.logger import get_logger  # type: ignore

logger = get_logger(__name__)

try:
    from pymodbus.client import ModbusTcpClient  # pymodbus>=3
    HAS_MODBUS = True
except Exception:
    HAS_MODBUS = False

try:
    from adapters.writer import write_jsonl
except Exception:
    import os
    sys.path.append(os.getcwd())
    from adapters.writer import write_jsonl  # type: ignore

def main():
    logger.info('starting modbus_reader.py')
    ap = argparse.ArgumentParser(description="Modbus TCP reader → JSONL")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=502)
    ap.add_argument("--unit", type=int, default=1)
    ap.add_argument("--address", type=int, default=0)  # starting register
    ap.add_argument("--count", type=int, default=10)   # number of registers
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not HAS_MODBUS:
        print("pymodbus not installed. pip install pymodbus", file=sys.stderr)
        sys.exit(2)

    client = ModbusTcpClient(args.host, port=args.port)
    ok = client.connect()
    if not ok:
        print("Failed to connect to Modbus device", file=sys.stderr)
        sys.exit(3)

    def gen():
        import time
        n = 0
        while True:
            rr = client.read_holding_registers(address=args.address, count=args.count, unit=args.unit)
            if rr.isError():
                rec = {"source": "Modbus", "error": str(rr), "ts": datetime.now(timezone.utc).isoformat()}
            else:
                rec = {"source": "Modbus", "unit": args.unit, "addr": args.address, "values": rr.registers, "ts": datetime.now(timezone.utc).isoformat()}
            yield rec
            n += 1
            if args.limit and n >= args.limit:
                break
            time.sleep(args.interval)
        client.close()

    write_jsonl(args.output, gen())

if __name__ == "__main__":
    main()