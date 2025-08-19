#!/usr/bin/env python3
"""
Anchor a partition MANIFEST's Merkle root into Bitcoin via an OP_RETURN output.

Requires a running bitcoind with wallet loaded (recommended), or provide RPC+wallet config.
Testnet is strongly recommended in development.

Usage:
  python tools/anchor_bitcoin.py \
    --manifest data/manifests/site=A/device=D/topic=vision/date=2025-08-19/hour=11/MANIFEST.json \
    --network testnet \
    --rpc-url http://127.0.0.1:18332 \
    --rpc-user user --rpc-pass pass \
    --wallet default \
    --fee-satvB 10

This will:
  - create a raw tx with OP_RETURN carrying "EAD1" + merkle_root (hex)
  - fund, sign, and broadcast using your node
  - update the MANIFEST.json with { "anchor": { "network", "txid", "anchored_utc" } }
  - write a receipt file ANCHOR.json alongside the MANIFEST
"""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import requests

MAGIC_PREFIX = "EAD1"  # Edge AI Data v1

def rpc_call(url, user, pw, method, params=None, wallet=None):
    if params is None:
        params = []
    headers = {"content-type": "application/json"}
    if wallet:
        # append /wallet/<name> to URL
        if not url.rstrip("/").endswith(f"/wallet/{wallet}"):
            if url.endswith("/"):
                url = url + f"wallet/{wallet}"
            else:
                url = url + f"/wallet/{wallet}"
    payload = {"jsonrpc": "1.0", "id": "anchor", "method": method, "params": params}
    r = requests.post(url, headers=headers, data=json.dumps(payload), auth=(user, pw), timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"RPC {method} failed: HTTP {r.status_code} {r.text[:200]}")
    data = r.json()
    if data.get("error"):
        raise RuntimeError(f"RPC {method} error: {data['error']}")
    return data["result"]

def create_opreturn_tx(rpc, wallet, data_hex, fee_satvB=None):
    # 1) createrawtransaction with only a data output
    outputs = [{"data": data_hex}]
    raw = rpc("createrawtransaction", [[], outputs], wallet=wallet)

    # 2) fundrawtransaction lets node pick inputs & change; try new key 'fee_rate' first (BTC/kvB), else 'feeRate'
    opts_list = []
    if fee_satvB is not None:
        # Convert sat/vB -> BTC/kvB: 1 sat/vB = 0.00001 BTC/kvB
        btc_per_kvb = float(fee_satvB) * 0.00001
        opts_list = [{"fee_rate": btc_per_kvb}, {"feeRate": btc_per_kvb}]  # try both
    else:
        opts_list = [{}]

    funded = None
    for opts in opts_list:
        try:
            funded = rpc("fundrawtransaction", [raw, opts], wallet=wallet)
            break
        except Exception as e:
            funded = None
            last_err = e
    if funded is None:
        raise RuntimeError(f"fundrawtransaction failed: {last_err}")

    # 3) signrawtransactionwithwallet
    signed = rpc("signrawtransactionwithwallet", [funded["hex"]], wallet=wallet)
    if not signed.get("complete"):
        raise RuntimeError("signrawtransactionwithwallet incomplete")
    # 4) sendrawtransaction
    txid = rpc("sendrawtransaction", [signed["hex"]], wallet=wallet)
    return txid, signed["hex"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="Path to MANIFEST.json to anchor")
    ap.add_argument("--network", default="testnet", choices=["mainnet", "testnet", "signet", "regtest"])
    ap.add_argument("--rpc-url", required=True, help="bitcoind RPC URL (e.g., http://127.0.0.1:18332 for testnet)")
    ap.add_argument("--rpc-user", required=True)
    ap.add_argument("--rpc-pass", required=True)
    ap.add_argument("--wallet", default="")
    ap.add_argument("--fee-satvB", type=float, default=10.0, help="Target fee rate (sat/vB), default 10")
    args = ap.parse_args()

    man_path = Path(args.manifest).resolve()
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    root = manifest.get("merkle_root")
    if not root or len(root) != 64:
        raise SystemExit("Manifest missing merkle_root (64 hex chars). Run tools/update_manifest.py first.")

    data_hex = MAGIC_PREFIX + root  # small header + 32-byte root
    #def rpc(lambda, method, params=None, wallet=None):
        #rpc_call(args.rpc_url, args.rpc_user, args.rpc_pass, method, params, wallet or args.wallet)

    def rpc(method, params=None, wallet=None):
        return rpc_call(
        args.rpc_url, args.rpc_user, args.rpc_pass, method, params, wallet or args.wallet
    )

    import sys
    try:
        txid, rawhex = create_opreturn_tx(rpc, args.wallet, data_hex, fee_satvB=args.fee_satvB)
    except Exception as e:
        print(f"Error in create_opreturn_tx: {e}")
        sys.exit(1)

    #txid, rawhex = create_opreturn_tx(rpc, args.wallet, data_hex, fee_satvB=args.fee_satvB)

    anchored = {
        "network": args.network,
        "txid": txid,
        "anchored_utc": datetime.now(timezone.utc).isoformat(),
        "op_return_hex": data_hex,
    }
    manifest["anchor"] = anchored
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    receipt = man_path.parent / "ANCHOR.json"
    receipt.write_text(json.dumps({
        "manifest": str(man_path),
        "merkle_root": root,
        "anchor": anchored,
        "rawtx_hex": rawhex[:120] + "...",
    }, indent=2), encoding="utf-8")

    print("Anchored txid:", txid)
    print("Updated manifest at:", man_path)
    print("Receipt at:", receipt)

if __name__ == "__main__":
    main()
