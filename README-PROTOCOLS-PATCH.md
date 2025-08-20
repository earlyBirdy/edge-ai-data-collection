## Supported Protocol Adapters (New)

This patch adds first-class scaffolding for **binary / legacy protocols** and **enterprise connectors**:

- **CAN bus** (`python-can`) → `adapters/can_reader.py`
- **Modbus TCP** (`pymodbus`) → `adapters/modbus_reader.py`
- **PCAP live capture** (`scapy`) → `adapters/pcap_reader.py`
- **Syslog UDP listener** (stdlib) → `adapters/syslog_listener.py`
- **OPC UA** (`asyncua`) → `adapters/opcua_reader.py`
- **ERP – Odoo** via XML‑RPC (stdlib) → `adapters/erp_odoo_reader.py`

All adapters emit **JSONL** records suitable for downstream validation and Parquet conversion.

### Quickstart
```bash
# Example: Modbus (reads holding registers and emits JSONL)
python tools/run_adapter.py modbus --host 192.168.1.10 --unit 1 --address 0 --count 10 --output data/samples/modbus/latest.jsonl

# Example: CAN (Linux SocketCAN)
python tools/run_adapter.py can --channel can0 --bustype socketcan --bitrate 500000 --output data/samples/can/capture.jsonl

# Example: PCAP
python tools/run_adapter.py pcap --iface eth0 --filter "tcp port 80" --count 100 --output data/samples/pcap/http.jsonl

# Example: Syslog listener (UDP 5140)
python tools/run_adapter.py syslog --host 0.0.0.0 --port 5140 --output data/samples/syslog/events.jsonl

# Example: OPC UA
python tools/run_adapter.py opcua --endpoint opc.tcp://localhost:4840 --nodes ns=2;i=2 ns=2;i=3 --output data/samples/opcua/readings.jsonl

# Example: ERP (Odoo)
python tools/run_adapter.py erp_odoo --url http://odoo.local:8069 --db mydb --user admin --password secret \  --model res.partner --domain "[]" --fields '["name","create_date"]' --limit 10 \  --output data/samples/erp/partners.jsonl
```

### Optional Dependencies
Add these to your environment as needed:
```
python-can
pymodbus>=3
scapy
asyncua
```
Odoo XML‑RPC uses Python stdlib. PCAP capture may require root or appropriate capabilities.

---
