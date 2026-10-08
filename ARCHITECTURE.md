# Architecture

How the Pilot 2 telemetry page works, for developers. For setup, see [README.md](README.md).

## Overview

```
 .env ──► web container (nginx) ──► page + config.js ──► DJI Pilot 2 on the RC
                                                              │
                                    licence check ◄───────────┤ (DJI servers)
                                                              │
                                    MQTT broker   ◄───────────┘ telemetry
```

The page (`web/index.html`) never talks to the broker. It only calls Pilot 2's JavaScript
bridge (`window.djiBridge`), and Pilot 2 opens the MQTT connection and sends the telemetry.

## Config from `.env`

On start, the `web` container runs `nginx/40-page-config.sh`, which writes the `.env` values
into `config.js` as `window.PAGE_CONFIG`. The page loads it and fills in the fields.

A value saved on the controller (from the last **Connect**) wins over `config.js`.
**Forget saved details** clears the saved values.

## Connect sequence

When the pilot taps **Connect**, the page calls Pilot 2's bridge:

1. `platformVerifyLicense(appId, appKey, license)`: Pilot 2 checks the licence with DJI.
   Nothing else works until this succeeds.
2. `platformLoadComponent("thing", {host, username, password, connectCallback})`:
   Pilot 2 connects to the broker and reports back through the callback.

**Disconnect** calls `platformUnloadComponent("thing")`. The status lights are refreshed every 5 seconds.

Outside Pilot 2 there is no bridge, so the page uses a fake one and shows "Preview mode".

## What Pilot 2 sends to the broker

`<sn>` is a device serial number.

| Topic                              | Content |
|------------------------------------|---------|
| `sys/product/<rc_sn>/status`       | `update_topo`: the controller is online, with its aircraft. |
| `sys/product/<rc_sn>/status_reply` | The back-end's reply to `update_topo`. |
| `thing/product/<sn>/osd`           | Position and flight data, about every 2 s. |
| `thing/product/<sn>/state`         | Device state changes. |

Some back-end must reply to `update_topo`, or Pilot 2 may not send the aircraft's telemetry.

## Testing services

Only for testing, not part of the real setup:

- **`broker`**: Mosquitto with password login, TCP on 1883 and WebSocket on 8083.
- **`watcher`**: prints aircraft positions and replies to `update_topo`.
  Set `REPLY_TOPO=false` in `.env` if another back-end already replies.
