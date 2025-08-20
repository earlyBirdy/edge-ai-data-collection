#!/usr/bin/env python3
"""
Video Recognition Pipeline

Extract frames from a video every N milliseconds and save them
into a structured output directory.
"""

import argparse
import os
import sys
import time
from pathlib import Path

try:
    import cv2
except ImportError:
    cv2 = None


def extract_frames(video_path: str, out_dir: str, every_ms: int = 1000):
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) is required. Install with `pip install opencv-python`")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    os.makedirs(out_dir, exist_ok=True)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0  # fallback

    frame_interval = int(fps * every_ms / 1000.0)
    if frame_interval < 1:
        frame_interval = 1

    frame_idx = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            ts_ms = int((frame_idx / fps) * 1000)
            out_file = Path(out_dir) / f"frame_{ts_ms:09d}.jpg"
            cv2.imwrite(str(out_file), frame)
            saved += 1

        frame_idx += 1

    cap.release()
    return saved


def main():
    ap = argparse.ArgumentParser(description="Video recognition / frame extractor")
    ap.add_argument("--input", required=True, help="Path to input video")
    ap.add_argument("--out", required=True, help="Directory to save frames")
    ap.add_argument("--every_ms", type=int, default=1000, help="Extract frame every N milliseconds")
    args = ap.parse_args()

    start = time.time()
    saved = extract_frames(args.input, args.out, args.every_ms)
    elapsed = time.time() - start

    print(f"✅ Extracted {saved} frames into {args.out} in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
