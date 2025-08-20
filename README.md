
# Why This Repository?

This repository exists to provide a practical, extensible framework for collecting, validating, and managing data at the edge for AI and IoT applications. In modern industrial and enterprise environments, data must be gathered reliably from sensors and systems, validated against schemas, and prepared for downstream use in analytics, training, and decision-making pipelines.

By maintaining structured, schema-validated JSONL samples and tools, this project helps ensure that:
- Edge devices can integrate smoothly with centralized AI/ML workflows
- Data pipelines remain consistent and machine-readable
- Developers can easily extend support for new sensor types and environments
- Enterprises can maintain auditability and compliance for sensitive workloads
- **On-chain anchoring of data (Bitcoin)** is supported for enterprise-grade trust, tamper-evidence, and regulatory assurance


# Edge AI Data Collection (Enhanced) and Supported Protocol Adapters

Fast, secure, and auditable data collection for edge devices with **tiered storage**:
- **Hot**: JSONL / Protobuf framed logs for ultra-fast append and tailing
- **Warm/Batch**: Parquet (+ zstd) for analytics and ML features
- **Governed**: JSON Schema / Avro contracts, signed manifests, and lineage-friendly layout

> This package adds sample files, schemas, and scaffolding (Docker, CI) to help you run and extend the repo quickly.

This repository now includes **binary/legacy protocol** and **enterprise** adapters, all emitting JSONL for downstream validation and Parquet conversion:

- **CAN bus** (`python-can`) → `adapters/can_reader.py`
- **Modbus TCP** (`pymodbus`) → `adapters/modbus_reader.py`
- **PCAP** live capture (`scapy`) → `adapters/pcap_reader.py`
- **Syslog** UDP listener (stdlib) → `adapters/syslog_listener.py`
- **OPC UA** (`asyncua`) → `adapters/opcua_reader.py` (SCADA-compatible)
- **ERP – Odoo** via XML-RPC (stdlib) → `adapters/erp_odoo_reader.py`


## Supported data & log formats

| Layer | Format | Use case |
|---|---|---|
| Hot logs | **JSONL** (`*.jsonl` / `*.jsonl.zst`) | Append-only events, decisions, ops logs |
| Hot streams (binary) | **Protobuf** (`*.pbr`) | High-rate sensor readings (compact, schema’d) |
| Batch analytics | **Parquet** (`*.parquet`, zstd) | Columnar storage for queries and features |
| Governance | **JSON Schema / Avro** (`*.schema.json` / `*.avsc`) | Data contracts & validation |
| Ops logs | **LOG** (`*.log`) | Process/ingestion logs |
| Media (optional) | **JPEG/PNG, MP4** | Vision/audio artifacts with sidecar JSON |


## Paths & partitioning

```
data/
  samples/
    hot/temperature/2025-08-19/temperature-2025-08-19T11-00.jsonl
    hot/ops/ingestion-2025-08-19.log
    batch/site=A/device=D/topic=temperature/date=2025-08-19/hour=11/part-000.parquet
  manifests/
    site=A/device=D/topic=temperature/date=2025-08-19/hour=11/MANIFEST.json
schema/
  temperature.schema.json
  temperature.avsc
adapters/
  opcua/README.md
  odoo/README.md
  sap/README.md
decision_engine/
  README.md
  engine.py (interface placeholder)
```

**Partitioning (batch):** `site=<id>/device=<id>/topic=<name>/date=YYYY-MM-DD/hour=HH/part-*.parquet`


## Minimal conventions
- **Compression**: zstd across Parquet; gzip/zstd on rotated JSONL (`*.jsonl.zst`)
- **Timestamps**: UTC, ISO-8601 in JSONL; INT64 in Parquet with TZ meta
- **Schemas**: keep `schema_fingerprint` (SHA-256) in file metadata/headers
- **Manifests**: per partition directory with per-file SHA-256 + Merkle root
- **Rotation**: JSONL every 100 MB or 15 min; Parquet target 128–512 MB files


## Quick start

```bash
# Modbus (reads holding registers)
python tools/run_adapter.py modbus --host 192.168.1.10 --unit 1 --address 0 --count 10   --output data/samples/modbus/latest.jsonl

# CAN (Linux SocketCAN)
python tools/run_adapter.py can --channel can0 --bustype socketcan --bitrate 500000   --output data/samples/can/capture.jsonl

# PCAP (capture 100 HTTP packets)
python tools/run_adapter.py pcap --iface eth0 --filter "tcp port 80" --count 100   --output data/samples/pcap/http.jsonl

# Syslog listener (UDP 5140)
python tools/run_adapter.py syslog --host 0.0.0.0 --port 5140   --output data/samples/syslog/events.jsonl

# OPC UA
python tools/run_adapter.py opcua --endpoint opc.tcp://localhost:4840   --nodes ns=2;i=2 ns=2;i=3   --output data/samples/opcua/readings.jsonl

# ERP (Odoo)
python tools/run_adapter.py erp_odoo --url http://odoo.local:8069 --db mydb   --user admin --password secret   --model res.partner --domain "[]" --fields '["name","create_date"]' --limit 10   --output data/samples/erp/partners.jsonl
```

> Install optional dependencies as needed:
>
> ```bash
> pip install -r requirements.txt
> # or selectively:
> pip install python-can pymodbus scapy asyncua
> ```

### Docker
```bash
docker build -t edge-ai-data:latest .
docker run --rm -v $PWD/data:/app/data edge-ai-data:latest python -m src.cli ingest --config ./configs/example.yaml
```

### Local (Python)
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m src.cli ingest --config ./configs/config.yaml
```

## Validation

**JSON Schema**:
```bash
python tools/validate_jsonl.py --schema ./schema/temperature.schema.json --input ./data/samples/hot/temperature/2025-08-19/temperature-2025-08-19T04-00.jsonl
```

**Avro (optional)**: use `fastavro` for round-trip tests.

## Decision engine interface

See `decision_engine/engine.py` for the interface. You can drop in rule packs and model runners (ONNX/TensorRT).

## CI

`.github/workflows/ci.yml` runs lint, type checks, and smoke tests; customize as needed.

---


### Jupyter Lab (zero-setup via Docker)

**Makefile route**
```bash
make lab              # builds the image and launches JupyterLab on http://localhost:8888
# or run in background:
make lab-detach
make stop             # stop detached lab
```

**docker-compose route**
```bash
docker compose up jupyter
# open http://localhost:8888
```

> Jupyter starts without a token for local development. For remote servers, set a token/password.


## Vision (Image & Video Recognition)

Run lightweight recognition that writes JSONL detections and optional annotated frames.

**Images**
```bash
python -m vision.pipelines.image_recognition --input ./data/media/images --out ./data/samples/hot/vision
```

**Video**
```bash
python -m vision.pipelines.video_recognition --input ./data/media/video/sample.mp4 --out ./data/samples/hot/vision --every_ms 500
```


### Annotated Frames

When running vision pipelines, annotated frames (with drawn boxes & labels) are saved under:

```
data/samples/hot/vision/frames/
```

Each image or sampled video frame gets a `*-annot.png` showing detected objects with bounding boxes and confidence scores.

Useful for **smart factory data analysis** where visual confirmation of detections is important.


### Vision frame annotations

Add `--annotate` to save PNGs with bounding boxes & labels. Optionally set `--frames_out` (defaults to `<out>/frames`).

**Images**
```bash
python -m vision.pipelines.image_recognition --input ./data/media/images   --out ./data/samples/hot/vision --annotate --frames_out ./data/samples/hot/vision/frames
```

**Video**
```bash
python -m vision.pipelines.video_recognition --input ./data/media/video/sample.mp4   --out ./data/samples/hot/vision --every_ms 500 --annotate --frames_out ./data/samples/hot/vision/frames
```


### Per-batch manifest (detections ↔ frames)

After running image/video pipelines (optionally with `--annotate`), create a **partition manifest**:

```bash
python tools/update_manifest.py   --data-root .   --outdir ./data/samples/hot/vision   --site A --device D --topic vision   --date $(date +%F) --hour $(date +%H)
```

This writes `data/manifests/site=A/device=D/topic=vision/date=YYYY-MM-DD/hour=HH/MANIFEST.json` including:
- SHA-256 for detection JSONL and annotated PNG frames
- A Merkle root across all files
- Linkage index: detection file → list of annotated frames referenced inside


## Tamper-evidence: Bitcoin anchoring (testnet or mainnet)

You can commit each partition's **Merkle root** on-chain via an `OP_RETURN` output.

> **Dev note:** Use **testnet** while developing. Mainnet costs real BTC.

**Anchor a manifest** (bitcoind JSON-RPC):
```bash
python tools/anchor_bitcoin.py \
  --manifest data/manifests/site=A/device=D/topic=vision/date=YYYY-MM-DD/hour=HH/MANIFEST.json \  --network testnet \  --rpc-url http://127.0.0.1:18332 \  --rpc-user <user> --rpc-pass <pass> \  --wallet <wallet_name> \  --fee-satvB 10
```

This updates the manifest with:
```json
"anchor": { "network": "testnet", "txid": "<txid>", "anchored_utc": "...", "op_return_hex": "EAD1<merkle_root>" }
```

**Verify** (via node RPC, or fallback REST API):
```bash
python tools/verify_anchor.py \
  --manifest data/manifests/site=A/device=D/topic=vision/date=YYYY-MM-DD/hour=HH/MANIFEST.json \  --network testnet \  --rpc-url http://127.0.0.1:18332 --rpc-user <user> --rpc-pass <pass> --wallet <wallet_name>
```

The OP_RETURN payload is `EAD1` + the 32-byte `merkle_root` from the manifest.


## Supported Example Machines

This repository is designed to work with a wide range of **industrial edge computing devices** that collect, validate, and stream sensor data.  
While the code is hardware-agnostic, the following classes of machines are good candidates for deployment:

### 1. Industrial PCs (IPC) & Rugged Edge Computers
- **Vendors**: Sintrones, Advantech, Aaeon, OnLogic, Vecow  
- **Use cases**: factory automation, AI inference at the edge, SCADA/PLC integration  
- **I/O support**: Ethernet, RS-232/485, CAN bus, GPIO, USB  

### 2. Embedded ARM / SoC Boards
- **Examples**: NVIDIA Jetson (Nano, Xavier, Orin), Raspberry Pi 5, BeagleBone, Orange Pi  
- **Use cases**: lightweight AI/ML inference, temperature/vibration data logging, low-power deployments  
- **I/O support**: CSI camera, SPI/I²C, GPIO, Wi-Fi/BT, LTE modules  

### 3. Gateways & Protocol Bridges
- **Examples**: Moxa UC series, HMS Anybus gateways, Siemens IoT2040  
- **Use cases**: protocol translation (OPC UA, Modbus, MQTT, EtherCAT), legacy machine integration  
- **I/O support**: Fieldbus, serial, Ethernet  

### 4. Specialized AI Accelerators
- **Examples**: Intel NUC + Movidius Myriad, Google Coral Dev Board, FPGA edge cards  
- **Use cases**: real-time AI workloads, defect detection, predictive maintenance  

---

> ⚠️ **Note**:  
This project assumes the target machine runs **Linux** (Ubuntu 20.04+ or Debian-based) with Python 3.9+.  
Windows can be supported with minor path/glob adjustments.  

---

## How to Add Your Own Machine
To integrate a new machine type:
1. Configure the device’s **data acquisition drivers** (e.g., sensor SDK, OPC UA client).
2. Point the data output to `data/samples/...` in JSONL format.  
3. Validate using:
   ```bash
   python tools/validate_jsonl.py --schema ./schema/temperature.schema.json --input ./data/samples/hot/temperature/{date_str}/temperature-{date_str}T{hour_str}-00.jsonl
   ```
4. (Optional) Extend `adapters/` with your device-specific protocol handler.

---
