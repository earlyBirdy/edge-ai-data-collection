#!/usr/bin/env python3
"""
Update or create a per-batch MANIFEST with SHA-256 of detection JSONL + annotated frames,
and a Merkle root across all included files. Links each detection record to its frame via
the "annotated_frame" field (if present).

Usage:
  python tools/update_manifest.py \
    --data-root . \
    --outdir ./data/samples/hot/vision \
    --site A --device D --topic vision \
    --date 2025-08-19 --hour 11
"""
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def merkle_root(hashes: List[str]) -> str:
    if not hashes:
        return ""
    nodes = [bytes.fromhex(h) for h in hashes]
    while len(nodes) > 1:
        nxt = []
        for i in range(0, len(nodes), 2):
            a = nodes[i]
            b = nodes[i + 1] if i + 1 < len(nodes) else a
            nxt.append(hashlib.sha256(a + b).digest())
        nodes = nxt
    return nodes[0].hex()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--data-root", default=".", help="Repo root (for relative paths in manifest)"
    )
    ap.add_argument(
        "--outdir", required=True, help="Folder where detections/frames were written"
    )
    ap.add_argument("--site", required=True)
    ap.add_argument("--device", required=True)
    ap.add_argument("--topic", default="vision")
    ap.add_argument("--date", default="")  # YYYY-MM-DD
    ap.add_argument("--hour", default="")  # HH (00-23)
    args = ap.parse_args()

    data_root = Path(args.data_root).resolve()
    outdir = Path(args.outdir).resolve()

    # Derive date/hour if omitted
    now = datetime.now(timezone.utc)
    date = args.date or now.strftime("%Y-%m-%d")
    hour = args.hour or now.strftime("%H")

    # Collect files: JSONL detections and annotated frames (PNGs)
    detections = sorted(outdir.rglob("vision-*.jsonl"))
    frames = sorted(outdir.rglob("*.png"))  # annotated frames convention

    # Build file entries
    files = []
    hashes = []

    def add_file(p: Path):
        rel = str(p.resolve().relative_to(data_root))
        h = sha256_file(p)
        files.append({"path": rel, "sha256": h, "size": p.stat().st_size})
        hashes.append(h)

    for p in detections:
        add_file(p)
    for p in frames:
        add_file(p)

    root = merkle_root(hashes)

    # Build detection-to-frame linkage summary by scanning a small sample
    # We don't rewrite detection files; we surface a high-level index
    # mapping detection file -> list of annotated frames seen inside.
    linkage = []
    for det in detections:
        ann = []
        try:
            with open(det, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    af = obj.get("annotated_frame")
                    if af:
                        try:
                            rel_af = str(Path(af).resolve().relative_to(data_root))
                        except Exception:
                            rel_af = af
                        ann.append(rel_af)
        except Exception:
            pass
        linkage.append(
            {
                "detection_file": str(det.resolve().relative_to(data_root)),
                "annotated_frames": ann,
            }
        )

    manifest_dir = (
        data_root
        / "data"
        / "manifests"
        / f"site={args.site}"
        / f"device={args.device}"
        / f"topic={args.topic}"
        / f"date={date}"
        / f"hour={hour}"
    )
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "MANIFEST.json"

    manifest = {
        "created_utc": now.isoformat(),
        "partition": {
            "site": args.site,
            "device": args.device,
            "topic": args.topic,
            "date": date,
            "hour": hour,
        },
        "files": files,
        "merkle_root": root,
        "linkage": linkage,
        "notes": "Detections/frames gathered from outdir; paths are relative to data-root.",
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Dummy signature
    sig_path = manifest_dir / "MANIFEST.sig"
    with open(sig_path, "w", encoding="utf-8") as f:
        f.write(hashlib.sha256((root + "|signed").encode()).hexdigest())

    print("Wrote", manifest_path)


if __name__ == "__main__":
    main()
