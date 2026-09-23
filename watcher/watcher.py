"""
Watches DJI Cloud API traffic on an MQTT broker.

- Prints the aircraft position from thing/product/<sn>/osd
- Answers sys/product/<gateway_sn>/status (update_topo), the "device online"
  handshake Pilot 2 sends when it connects. Set REPLY_TOPO=false if your
  partner's backend already answers it, so the controller doesn't get two replies.
"""
import json
import os
import ssl
import time

import paho.mqtt.client as mqtt

HOST = os.getenv("BROKER_HOST", "broker")
PORT = int(os.getenv("BROKER_PORT", "1883"))
USE_TLS = os.getenv("BROKER_TLS", "false").lower() == "true"
USER = os.getenv("MQTT_USER", "")
PASS = os.getenv("MQTT_PASS", "")
REPLY_TOPO = os.getenv("REPLY_TOPO", "true").lower() == "true"

aircraft_sns = set()   # learned from update_topo
controller_sns = set()
last_print = {}        # sn -> time of last printed osd line


def log(*args):
    print(time.strftime("%H:%M:%S"), *args, flush=True)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        log(f"Broker refused connection: {reason_code}")
        return
    log(f"Connected to {HOST}:{PORT}")
    client.subscribe("sys/product/+/status")
    client.subscribe("thing/product/+/osd")
    client.subscribe("thing/product/+/state")


def handle_status(client, sn, msg):
    if msg.get("method") != "update_topo":
        return
    controller_sns.add(sn)
    subs = msg.get("data", {}).get("sub_devices", []) or []
    for d in subs:
        if d.get("sn"):
            aircraft_sns.add(d["sn"])
    if subs:
        log(f"Controller {sn} online, aircraft: {', '.join(d.get('sn', '?') for d in subs)}")
    else:
        log(f"Controller {sn} online, no aircraft connected yet")

    if REPLY_TOPO:
        reply = {
            "tid": msg.get("tid"),
            "bid": msg.get("bid"),
            "timestamp": int(time.time() * 1000),
            "method": "update_topo",
            "data": {"result": 0},
        }
        client.publish(f"sys/product/{sn}/status_reply", json.dumps(reply))
        log(f"Sent update_topo reply to {sn}")


def handle_osd(sn, msg):
    data = msg.get("data", {}) or {}
    lat, lon = data.get("latitude"), data.get("longitude")
    if lat is None or lon is None:
        return
    now = time.time()
    if now - last_print.get(sn, 0) < 1:
        return
    last_print[sn] = now

    who = "AIRCRAFT" if sn in aircraft_sns else ("CONTROLLER" if sn in controller_sns else "DEVICE")
    parts = [f"{who} {sn}", f"lat={lat:.7f}", f"lon={lon:.7f}"]
    if "height" in data:
        parts.append(f"height={data['height']:.1f}m")
    if "elevation" in data:
        parts.append(f"rel_alt={data['elevation']:.1f}m")
    if "attitude_head" in data:
        parts.append(f"heading={data['attitude_head']}")
    if "horizontal_speed" in data:
        parts.append(f"speed={data['horizontal_speed']}m/s")
    log("  ".join(parts))


def on_message(client, userdata, m):
    try:
        msg = json.loads(m.payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        log(f"Non-JSON message on {m.topic}")
        return

    parts = m.topic.split("/")
    sn = parts[2] if len(parts) > 2 else "?"
    kind = parts[3] if len(parts) > 3 else ""

    if parts[0] == "sys" and kind == "status":
        handle_status(client, sn, msg)
    elif kind == "osd":
        handle_osd(sn, msg)
    elif kind == "state":
        log(f"State change from {sn}: {', '.join(list((msg.get('data') or {}).keys())[:6])}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"watcher-{int(time.time())}")
    if USER:
        client.username_pw_set(USER, PASS)
    if USE_TLS:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    while True:
        try:
            log(f"Connecting to {HOST}:{PORT} (tls={USE_TLS})")
            client.connect(HOST, PORT, keepalive=60)
            client.loop_forever(retry_first_connection=True)
        except Exception as e:
            log(f"Connection error: {e}; retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
