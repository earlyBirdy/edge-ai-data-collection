import argparse
import sys
from pathlib import Path

try:
    from common.logger import get_logger
except Exception:
    import os
    sys.path.append(os.getcwd())
    from common.logger import get_logger  # type: ignore

logger = get_logger(__name__)

try:
    import cv2
except ImportError:
    cv2 = None


def extract_frames(video_path: str, output_dir: str, every_ms: int = 1000):
    """
    Extract frames from video at fixed intervals.
    """
    if cv2 is None:
        raise RuntimeError("OpenCV is required but not installed.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        raise RuntimeError("Cannot determine FPS of video")

    frame_interval = int((every_ms / 1000.0) * fps)
    frame_idx = 0
    saved = []

    logger.info(f"Starting extraction from {video_path} every {every_ms}ms")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            frame_file = output_dir / f"frame-{frame_idx:08d}.png"
            cv2.imwrite(str(frame_file), frame)
            saved.append(str(frame_file))
            logger.debug(f"Saved {frame_file}")

        frame_idx += 1

    cap.release()
    logger.info(f"Extracted {len(saved)} frames -> {output_dir}")
    return saved


def main():
    logger.info("starting video_recognition.py")
    ap = argparse.ArgumentParser(description="Video recognition / frame extractor")
    ap.add_argument("--input", required=True, help="Path to input video")
    ap.add_argument("--out", required=True, help="Output directory for frames")
    ap.add_argument("--every_ms", type=int, default=1000, help="Interval in milliseconds between frames")
    args = ap.parse_args()

    extract_frames(args.input, args.out, args.every_ms)


if __name__ == "__main__":
    main()
