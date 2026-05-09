### config.py
#
import os
import json
from tkinter import messagebox
#
try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError("paho-mqtt is required. Install it with: pip install paho-mqtt")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

DEFAULT_CONFIG = {
    "mqtt": {
        # "server": "192.168.1.29",
        "server": "127.0.0.1",
        "port": 1883,
        "pub_topic": "games/mouse/position",
        "sub_topic": "games/mouse/position"
    }
}

def parse_mqtt_host(server_string):
    if server_string.startswith("tcp://"):
        return server_string.replace("tcp://", "")
    return server_string

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        mqtt_cfg = cfg.get("mqtt", {})
        server = mqtt_cfg.get("server", DEFAULT_CONFIG["mqtt"]["server"])
        port = mqtt_cfg.get("port", DEFAULT_CONFIG["mqtt"]["port"])
        return {
            "server": server,
            "port": port,
            "pub_topic": mqtt_cfg.get("pub_topic", DEFAULT_CONFIG["mqtt"]["pub_topic"]),
            "sub_topic": mqtt_cfg.get("sub_topic", DEFAULT_CONFIG["mqtt"]["sub_topic"]),
        }
    except FileNotFoundError:
        return DEFAULT_CONFIG["mqtt"]
    except Exception as exc:
        messagebox.showwarning("MQTT Config", f"Unable to read config.json: {exc}\nUsing defaults.")
        return DEFAULT_CONFIG["mqtt"]
    
