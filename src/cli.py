# src/cli.py
import argparse
import json
import sys
from .collector import run_collector
from .batcher import run_batcher
from .decision_engine.engine import load_policy, decide

def cmd_decide(args):
    policy = load_policy(args.policy)
    event = json.loads(args.event) if args.event else json.loads(sys.stdin.read())
    res = decide(event, policy)
    print(json.dumps(res, indent=2))

def main():
    p = argparse.ArgumentParser(description="Edge AI Data Collection CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("collect", help="Run MQTT -> JSONL collector")
    pc.add_argument("--config", required=True, help="Path to config.yaml")

    pb = sub.add_parser("batch", help="Convert JSONL -> Parquet")
    pb.add_argument("--config", required=True, help="Path to config.yaml")

    pd = sub.add_parser("decide", help="Run a single decision on an event JSON")
    pd.add_argument("--policy", required=True, help="Path to policies.yaml")
    pd.add_argument("--event", help='Inline JSON string (if not provided, read from stdin)')

    args = p.parse_args()

    if args.cmd == "collect":
        run_collector(args.config)
    elif args.cmd == "batch":
        run_batcher(args.config)
    elif args.cmd == "decide":
        cmd_decide(args)

if __name__ == "__main__":
    main()
