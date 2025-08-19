#!/usr/bin/env python3
"""
Verify that a manifest's merkle_root was committed in a given Bitcoin tx's OP_RETURN.
Prefers node RPC; falls back to public REST APIs if configured.

Usage:
  python tools/verify_anchor.py --manifest <MANIFEST.json> \
    --rpc-url http://127.0.0.1:18332 --rpc-user user --rpc-pass pass --wallet default
or
  python tools/verify_anchor.py --manifest <MANIFEST.json> --rest-api mempool --network testnet
"""
import argparse
import json
import sys
import requests
from pathlib import Path

def rpc_call(url, user, pw, method, params=None, wallet=None):
    if params is None:
        params = []
    headers = {"content-type": "application/json"}
    if wallet:
        if not url.rstrip("/").endswith(f"/wallet/{wallet}"):
            if url.endswith("/"):
                url = url + f"wallet/{wallet}"
            else:
                url = url + f"/wallet/{wallet}"
    payload = {"jsonrpc":"1.0","id":"verify","method":method,"params":params}
    r = requests.post(url, headers=headers, data=json.dumps(payload), auth=(user,pw), timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data["result"]

def extract_op_returns_from_verbose_tx(tx_verbose):
    outs = []
    for v in tx_verbose.get("vout", []):
        spk = v.get("scriptPubKey", {})
        asm = spk.get("asm","")
        # Example: "OP_RETURN 454144313234..." (hex after opcode)
        parts = asm.split()
        if parts and parts[0] == "OP_RETURN" and len(parts) > 1:
            outs.append(parts[1])
    return outs

def fetch_tx_hex_rest_mempool(network, txid):
    base = "https://mempool.space"
    if network == "testnet":
        base = "https://mempool.space/testnet"
    elif network == "signet":
        base = "https://mempool.space/signet"
    url = f"{base}/api/tx/{txid}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    tx = r.json()
    outs = []
    for vout in tx.get("vout", []):
        asm = vout.get("scriptpubkey_asm", "")
        parts = asm.split()
        if parts and parts[0] == "OP_RETURN" and len(parts) > 1:
            outs.append(parts[1])
    return outs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--network", default="testnet", choices=["mainnet","testnet","signet","regtest"])
    ap.add_argument("--rpc-url", default="")
    ap.add_argument("--rpc-user", default="")
    ap.add_argument("--rpc-pass", default="")
    ap.add_argument("--wallet", default="")
    ap.add_argument("--rest-api", default="mempool", choices=["mempool"])
    args = ap.parse_args()

    man = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    anchor = man.get("anchor", {})
    root = man.get("merkle_root")
    txid = anchor.get("txid")
    data_hex = anchor.get("op_return_hex") or ""

    if not root or not txid:
        print("Manifest missing merkle_root or anchor.txid", file=sys.stderr)
        sys.exit(2)

    # Try RPC first if provided
    oprets = []
    if args.rpc_url and args.rpc_user:
        try:
            tx_verbose = rpc_call(args.rpc_url, args.rpc_user, args.rpc_pass, "getrawtransaction", [txid, True], wallet=args.wallet)
            oprets = extract_op_returns_from_verbose_tx(tx_verbose)
        except Exception as e:
            print("RPC verify failed, falling back to REST:", e, file=sys.stderr)

    if not oprets:
        # REST fallback
        try:
            oprets = fetch_tx_hex_rest_mempool(args.network, txid)
        except Exception as e:
            print("REST verify failed:", e, file=sys.stderr)
            sys.exit(3)

    want = data_hex or ("EAD1" + root)
    ok = any(hexstr.upper().endswith(root.upper()) and hexstr.upper().startswith(want[:4].upper()) for hexstr in oprets)

    print("Anchored merkle_root:", root)
    print("TXID:", txid)
    print("Found OP_RETURN payloads:", oprets)
    print("Verification:", "PASS ✅" if ok else "FAIL ❌")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
