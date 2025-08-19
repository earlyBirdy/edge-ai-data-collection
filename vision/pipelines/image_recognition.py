import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None

try:
    import onnxruntime as ort
except Exception:
    ort = None

def load_model(model_path: Path):
    if model_path and model_path.exists() and ort is not None:
        return ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    return None

def preprocess(img: Image.Image):
    # Simple center-crop + resize to 224x224, convert to RGB, normalize 0..1
    img = ImageOps.exif_transpose(img.convert("RGB"))
    img = ImageOps.fit(img, (224,224))
    arr = ( ( ( (list(img.getdata())) ) ) )
    # Convert to NCHW float32 [mock minimal to avoid numpy dependency]
    import array
    floats = array.array('f', [0.0]) * (224*224*3)
    for i, px in enumerate(arr):
        r,g,b = px
        floats[i*3+0] = r/255.0
        floats[i*3+1] = g/255.0
        floats[i*3+2] = b/255.0
    return floats

def mock_detect(img: Image.Image) -> List[Dict[str, Any]]:
    # Heuristic: use brightness to fake a "object" confidence
    px = img.resize((8,8)).convert("L")
    mean = sum(px.getdata()) / 64.0
    score = min(0.99, max(0.01, (mean/255.0)))
    return [{"label": "object", "score": score, "bbox": [0.1,0.1,0.8,0.8]}]


def draw_annotations(img, classes, out_path=None, label_color=(255,0,0)):
    from PIL import ImageDraw
    W, H = img.size
    dr = ImageDraw.Draw(img)
    for c in classes:
        bbox = c.get('bbox', [0.1,0.1,0.8,0.8])
        x,y,w,h = bbox
        x0,y0,x1,y1 = int(x*W), int(y*H), int((x+w)*W), int((y+h)*H)
        dr.rectangle([x0,y0,x1,y1], outline=label_color, width=2)
        lbl = f"{c.get('label','obj')}:{c.get('score',0):.2f}"
        dr.text((x0+3, y0+3), lbl, fill=label_color)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Folder of images")
    ap.add_argument("--out", required=True, help="Output folder for JSONL")
    ap.add_argument("--model", default="", help="Path to ONNX model (optional)")
    ap.add_argument("--device_id", default="D-123")
    ap.add_argument("--annotate", action="store_true", help="Save annotated frames (PNG)")
    ap.add_argument("--frames_out", default="", help="Output folder for annotated frames")
    ap.add_argument("--site", default="A")
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    model = load_model(Path(args.model)) if args.model else None

    if Image is None:
        print("PIL not available; install pillow.", file=sys.stderr)
        sys.exit(1)

    annot_dir = out_dir / 'frames'
    annot_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"vision-detections-{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')}.jsonl"
    with open(out_file, "w", encoding="utf-8") as out:
        for p in sorted(in_dir.rglob("*")):
            if p.suffix.lower() not in [".png", ".jpg", ".jpeg", ".bmp"]:
                continue
            try:
                img = Image.open(p)
                if model is None:
                    classes = mock_detect(img)
                else:
                    # Minimal example: you'd adapt to your model's input/output
                    # floats = preprocess(img)
                    # Using a fake output as example; proper mapping depends on model
                    classes = mock_detect(img)
                # Optionally draw annotations
                if args.annotate:
                    frames_out = Path(args.frames_out) if args.frames_out else (Path(args.out)/"frames")
                    annotated_path = frames_out / (p.stem + "-annotated.png")
                    draw_annotations(img.copy(), classes, annotated_path)

                rec = {
                    "annotated_frame": str(annotated_path) if args.annotate else None,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "source": "image",
                    "path": str(p),
                    "classes": classes,
                    "device_id": args.device_id,
                    "site": args.site
                }
                out.write(json.dumps(rec) + "\n")
                # Draw annotation
                try:
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(img)
                    for cls in classes:
                        x,y,w,h = cls.get("bbox",[0,0,1,1])
                        # bbox coords are normalized (0-1)
                        x0,y0 = int(x*img.width), int(y*img.height)
                        x1,y1 = int((x+w)*img.width), int((y+h)*img.height)
                        draw.rectangle([x0,y0,x1,y1], outline="red", width=2)
                        draw.text((x0,y0-10), f"{cls['label']} {cls['score']:.2f}", fill="red")
                    img.save(annot_dir / (p.stem + "-annot.png"))
                except Exception as e:
                    print("Annot fail", e, file=sys.stderr)
            except Exception as e:
                print("Failed on", p, e, file=sys.stderr)

    print("Wrote", out_file)

if __name__ == "__main__":
    main()
