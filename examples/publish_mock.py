import time
import json
import random
import paho.mqtt.client as mqtt

HOST="localhost"
PORT=1883
TOPIC="factory/sensor/event"

def main():
    c = mqtt.Client()
    c.connect(HOST, PORT, 60)
    c.loop_start()
    try:
        while True:
            payload = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": "lineA-press01",
                "temperature": round(random.uniform(65, 90), 2),
                "vibration": round(random.uniform(0.01, 0.25), 3),
                "anomaly": False
            }
            c.publish(TOPIC, json.dumps(payload))
            print("[mock] published", payload)
            time.sleep(2)
    except KeyboardInterrupt:
        print("[mock] stopped")

if __name__ == "__main__":
    main()
