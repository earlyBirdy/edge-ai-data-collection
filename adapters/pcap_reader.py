import argparse
import sys
from datetime import datetime, timezone
try:
    from scapy.all import sniff  # scapy
    HAS_SCAPY = True
except Exception:
    HAS_SCAPY = False

try:
    from adapters.writer import write_jsonl
except Exception:
    import os
    sys.path.append(os.getcwd())
    from adapters.writer import write_jsonl  # type: ignore

def main():
    ap = argparse.ArgumentParser(description="PCAP live capture → JSONL")
    ap.add_argument("--iface", default=None, help="Interface (e.g., eth0). If omitted, scapy default.")
    ap.add_argument("--filter", default=None, help="BPF filter, e.g., 'tcp port 80'")
    ap.add_argument("--count", type=int, default=0, help="Number of packets to capture (0 = infinite)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    if not HAS_SCAPY:
        print("scapy not installed. pip install scapy", file=sys.stderr)
        sys.exit(2)

    def pkthandler(pkt):
        raw = bytes(pkt)[:128].hex()
        return {
            "source": "PCAP",
            "iface": args.iface,
            "summary": pkt.summary(),
            "len": len(pkt),
            "raw_head_hex": raw,
            "ts": datetime.now(timezone.utc).isoformat()
        }

    def gen():
        captured = sniff(iface=args.iface, filter=args.filter, count=args.count, prn=None)
        for pkt in captured:
            yield pkthandler(pkt)

    write_jsonl(args.output, gen())

if __name__ == "__main__":
    main()
