import argparse
import sys
import asyncio
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
    from asyncua import Client  # opcua async client
    HAS_OPCUA = True
except Exception:
    HAS_OPCUA = False

try:
    from adapters.writer import write_jsonl
except Exception:
    import os
    sys.path.append(os.getcwd())
    from adapters.writer import write_jsonl  # type: ignore

async def run(endpoint, node_ids, output, limit):
    client = Client(url=endpoint)
    await client.connect()
    try:
        count = 0
        while True:
            rec = {"source": "OPC_UA", "endpoint": endpoint, "ts": datetime.now(timezone.utc).isoformat(), "values": {}}
            for nid in node_ids:
                node = client.get_node(nid)
                try:
                    val = await node.read_value()
                except Exception as e:
                    val = f"ERROR: {e}"
                rec["values"][nid] = val
            write_jsonl(output, [rec])
            count += 1
            if limit and count >= limit:
                break
            await asyncio.sleep(1.0)
    finally:
        await client.disconnect()

def main():
    logger.info('starting opcua_reader.py')
    ap = argparse.ArgumentParser(description="OPC UA reader → JSONL")
    ap.add_argument("--endpoint", required=True, help="opc.tcp://HOST:PORT")
    ap.add_argument("--nodes", nargs="+", required=True, help="Node IDs to read")
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not HAS_OPCUA:
        print("asyncua not installed. pip install asyncua", file=sys.stderr)
        sys.exit(2)

    asyncio.run(run(args.endpoint, args.nodes, args.output, args.limit))

if __name__ == "__main__":
    main()