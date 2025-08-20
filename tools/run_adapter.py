#!/usr/bin/env python3
import argparse, subprocess, sys
from pathlib import Path

ADAPTERS = {
    "can": "adapters/can_reader.py",
    "modbus": "adapters/modbus_reader.py",
    "pcap": "adapters/pcap_reader.py",
    "syslog": "adapters/syslog_listener.py",
    "opcua": "adapters/opcua_reader.py",
    "erp_odoo": "adapters/erp_odoo_reader.py",
}

def main():
    ap = argparse.ArgumentParser(description="Run an adapter by name")
    ap.add_argument("name", choices=ADAPTERS.keys())
    ap.add_argument("args", nargs=argparse.REMAINDER)
    ns = ap.parse_args()

    script = ADAPTERS[ns.name]
    cmd = [sys.executable, script] + ns.args
    raise SystemExit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
