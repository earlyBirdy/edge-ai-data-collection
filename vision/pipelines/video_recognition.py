#!/usr/bin/env python3
"""
Video Recognition Pipeline
Extract frames from video at fixed intervals and save them as images.
"""

import argparse
import os
import cv2


def extract_frames(video_path: str, out_dir: str, every_ms: int = 1000) -> int:
    """Extract frames every `every_ms` milliseconds from the video."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    os.makedirs(out_dir, exist_ok=True)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        raise RuntimeError(f"Cannot determine FPS for video: {video_path}")

    frame_interval = int(round(fps * every_ms / 1000.0))
    if frame_interval <= 0:
        frame_interval = 1

    frame_idx, saved = 0, 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            out_path = os.path.join(out_dir, f"frame_{frame_idx:06d}.jpg")
            cv2.imwrite(out_path, frame)
            saved += 1
        frame_idx += 1

    cap.release()
    return saved


def main():
    ap = argparse.ArgumentParser(description="Video recognition pipeline")
    ap.add_argument("--input", required=True, help="Input video file")
    ap.add_argument("--out", required=True, help="Output directory for frames")
    ap.add_argument("--every_ms", type=int, default=1000,
                    help="Interval in milliseconds between frames (default=1000)")
    args = ap.parse_args()

    try:
        saved = extract_frames(args.input, args.out, args.every_ms)
        print(f"✅ Saved {saved} frames into {args.out}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
