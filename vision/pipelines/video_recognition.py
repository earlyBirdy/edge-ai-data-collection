import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    import cv2
except Exception:
    cv2 = None

# Reuse heuristic from image pipeline via simple grayscale mean
def detect_frame(gray):
    mean = gray.mean() if gray is not None else 0.0
    score = max(0.01, min(0.99, float(mean)/255.0))
    return [{"label": "object", "score": score, "bbox": [0.1,0.1,0.8,0.8]}]

def draw_annotations_cv(frame, classes, color=(0,0,255)):
    import cv2
    H, W = frame.shape[:2]
    for c in classes:
        x,y,w,h = c.get('bbox',[0.1,0.1,0.8,0.8])
        x0,y0,x1,y1 = int(x*W), int(y*H), int((x+w)*W), int((y+h)*H)
        cv2.rectangle(frame, (x0,y0), (x1,y1), color, 2)
        lbl = f"{c.get('label','obj')}:{c.get('score',0):.2f}"
        cv2.putText(frame, lbl, (x0+5, max(15,y0+15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    return frame

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Video file (mp4/mov/avi)")
    ap.add_argument("--out", required=True, help="Output folder for JSONL")
    ap.add_argument("--every_ms", type=int, default=500, help="Sample every N ms")
    ap.add_argument("--device_id", default="D-123")
    ap.add_argument("--annotate", action="store_true", help="Save annotated frames (PNG)")
    ap.add_argument("--frames_out", default="", help="Output folder for annotated frames")
    ap.add_argument("--site", default="A")
    args = ap.parse_args()

    if cv2 is None:
        print("OpenCV not available; install opencv-python.", file=sys.stderr)
        sys.exit(1)

    cap = cv2.VideoCapture(str(args.input))
    if not cap.isOpened():
        print("Cannot open video:", args.input, file=sys.stderr)
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_interval = int((args.every_ms/1000.0) * fps)
    frame_idx = 0

    out_dir = Path(args.out)
    annot_dir = out_dir / 'frames'
    annot_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"vision-video-{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')}.jsonl"

    with open(out_file, "w", encoding="utf-8") as out:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % max(1, frame_interval) == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                classes = detect_frame(gray)
                # Optionally save annotated frame
                if args.annotate:
                    frames_out = Path(args.frames_out) if args.frames_out else (Path(args.out)/"frames")
                    frames_out.mkdir(parents=True, exist_ok=True)
                    annotated = draw_annotations_cv(frame.copy(), classes)
                    import cv2
                    frame_file = frames_out / f"frame-{frame_idx:08d}.png"
                    cv2.imwrite(str(frame_file), annotated)
                rec = {
                "annotated_frame": str(frame_file) if args.annotate else None,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "source": "video",
                    "path": str(Path(args.input)),
                    "frame_index": frame_idx,
                    "classes": classes,
                    "device_id": args.device_id,
                    "site": args.site
                }
                out.write(json.dumps(rec) + "\n")
                # Draw annotation
                try:
                    import cv2
                    frame_copy = frame.copy()
                    for cls in classes:
                        x,y,w,h = cls.get("bbox",[0,0,1,1])
                        x0,y0 = int(x*frame.shape[1]), int(y*frame.shape[0])
                        x1,y1 = int((x+w)*frame.shape[1]), int((y+h)*frame.shape[0])
                        cv2.rectangle(frame_copy,(x0,y0),(x1,y1),(0,0,255),2)
                        cv2.putText(frame_copy, f"{cls['label']} {cls['score']:.2f}", (x0,y0-5),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),1)
                    cv2.imwrite(str(annot_dir / f"frame-{frame_idx:06d}.png"), frame_copy)
                except Exception as e:
                    print("Annot fail", e, file=sys.stderr)
            frame_idx += 1

    cap.release()
    print("Wrote", out_file)

if __name__ == "__main__":
    main()
