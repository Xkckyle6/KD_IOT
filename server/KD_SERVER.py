import time
import json
import paho.mqtt.client as mqtt

BROKER = "127.0.0.1"
PORT = 1884
TOPIC = "test/device001/status"

received_messages = []

def on_connect(client, userdata, flags, rc):
    print(f"Connected with rc={rc}")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received on {msg.topic}: {payload}")
    received_messages.append(payload)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start()

time.sleep(1)

test_payload = {
    "test_id": "T001",
    "command": "ping",
    "timestamp": time.time()
}

client.publish(TOPIC, json.dumps(test_payload), qos=1)

time.sleep(2)

if received_messages:
    print("PASS: message received")
else:
    print("FAIL: no message received")

client.loop_stop()
client.disconnect()