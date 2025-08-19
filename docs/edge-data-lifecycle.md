# Edge AI Data Lifecycle

This diagram shows the flow of data from edge devices through hot/batch stages, governance, decision engine, and optional Bitcoin anchoring.

```mermaid
flowchart LR
  subgraph Edge_Device["Edge Device (Sensors & Cameras)"]
    S1[Sensor Streams<br/>(metrics, states)]
    C1[Camera Streams<br/>(images/video)]
  end

  subgraph Hot_Stage["Hot Stage (Append Logs)"]
    J1[JSONL events<br/>(telemetry, decisions)]
    P1[Protobuf frames<br/>(high-rate telemetry)]
    V1[Detections JSONL<br/>(vision results)]
    F1[Annotated Frames<br/>(PNG)]
  end

  subgraph Batch_Stage["Batch Stage (Analytics Store)"]
    Q1[Parquet Partitions<br/>site=/device=/topic=/date=/hour=]
    M1[Media Artifacts<br/>(MP4/JPG/PNG)]
  end

  subgraph Governance["Governance & Integrity"]
    SC[Schema Contracts<br/>(JSON Schema / Avro / .proto)]
    MF[Partition MANIFEST.json<br/>& MANIFEST.sig<br/>(SHA-256 + Merkle root)]
  end

  subgraph Decisions["Decision Engine @ Edge"]
    DE[Rules + ML Inference<br/>(e.g., ONNX/TensorRT)]
  end

  subgraph TamperProof["Tamper Evidence (Optional)"]
    BC[Bitcoin Anchor<br/>(OP_RETURN: EAD1 + merkle_root)]
  end

  S1 -->|append| J1
  S1 -->|binary| P1
  C1 -->|sample frames| V1
  C1 -->|optional| F1

  J1 -->|roll-up| Q1
  P1 -->|roll-up| Q1
  V1 -->|roll-up| Q1
  F1 --> M1

  SC --- J1
  SC --- P1
  SC --- Q1
  SC --- V1

  Q1 --> MF
  M1 --> MF
  V1 --> MF
  F1 --> MF

  J1 --> DE
  V1 --> DE
  Q1 --> DE

  MF -->|merkle_root| BC
```

The above shows the full data lifecycle: from **Edge Device → JSONL/Protobuf → Parquet/Media → Manifest → Decision Engine → Bitcoin Anchor**.
