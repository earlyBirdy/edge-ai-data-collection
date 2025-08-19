# Vision: Image & Video Recognition

This module adds **image** and **video** recognition pipelines that emit detections as JSONL and Parquet-ready rows.

- **Engine:** Uses **ONNX Runtime** if a model is provided. Falls back to a **mock heuristic** (edge-safe) when no model is present.
- **Inputs:**
  - Images: PNG/JPG
  - Video: MP4/MOV/AVI (requires OpenCV)
- **Outputs:**
  - JSONL detections (append-only)
  - Optional annotated frames (PNG) for inspection
  - Sidecar metadata `*.meta.json`

## Quick start

### Images
```bash
python -m vision.pipelines.image_recognition \
  --input ./data/media/images \  --out ./data/samples/hot/vision \  --model ./models/mobilenet.onnx   # optional; if omitted uses mock
```

### Video (frame sampling every N ms)
```bash
python -m vision.pipelines.video_recognition \  --input ./data/media/video/sample.mp4 \  --out ./data/samples/hot/vision \  --every_ms 500 \  --model ./models/mobilenet.onnx   # optional
```

## Format
Each detection record (JSONL) contains:
```json
{
  "ts": "2025-08-19T11:00:00Z",
  "source": "image|video",
  "path": "data/media/images/img-001.png",
  "classes": [{"label": "object", "score": 0.92, "bbox": [x,y,w,h]}],
  "device_id": "D-123",
  "site": "A"
}
```
