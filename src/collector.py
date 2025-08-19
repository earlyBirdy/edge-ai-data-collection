# src/collector.py
import json
import pathlib
import datetime
import paho.mqtt.client as mqtt
import yaml

def _ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

def _daily_path(hot_dir, prefix, ts_utc: datetime.datetime):
    day = ts_utc.strftime("%Y-%m-%d")
    return pathlib.Path(hot_dir) / f"{prefix}.{day}.jsonl"

def on_message_append_jsonl(hot_path: pathlib.Path, payload: bytes):
    try:
        obj = json.loads(payload.decode("utf-8"))
        line = json.dumps(obj, separators=(",", ":"))
        with hot_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print("[collector] ERROR decoding/appending:", e)

def run_collector(config_path: str):
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    mqtt_cfg = cfg["mqtt"]
    st = cfg["storage"]
    hot_dir = pathlib.Path(st["hot_dir"])
    _ensure_dir(hot_dir)
    prefix = st.get("file_prefix", "telemetry")

    def on_connect(client, userdata, flags, rc, properties=None):
        print("[collector] MQTT connected, rc=", rc)
        for t in mqtt_cfg["topics"]:
            client.subscribe(t, qos=0)
            print("[collector] subscribed:", t)

    def on_message(client, userdata, msg):
        ts = datetime.datetime.utcnow()
        hot_path = _daily_path(hot_dir, prefix, ts)
        on_message_append_jsonl(hot_path, msg.payload)

    client = mqtt.Client()
    if mqtt_cfg.get("username"):
        client.username_pw_set(mqtt_cfg["username"], mqtt_cfg.get("password"))
    # TLS can be added if mqtt_cfg['tls'] is True

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(mqtt_cfg["host"], int(mqtt_cfg["port"]), 60)
    print("[collector] running… (Ctrl+C to stop)")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("[collector] stopped")
