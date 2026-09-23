# Pilot 2 → MQTT telemetry test (Mavic 3T)

Three containers:

| Service   | What it does                                                      | Port(s)            |
|-----------|-------------------------------------------------------------------|--------------------|
| `web`     | Serves the page Pilot 2 opens under Open Platforms                 | 8080               |
| `broker`  | Local Mosquitto test broker, password required                    | 1883 (tcp), 8083 (ws) |
| `watcher` | Prints the aircraft position and answers Pilot 2's online handshake | –                  |

Test against the local broker first. Once that works, switch to your partner's broker.

## 1. Before you start

- A computer with Docker and Docker Compose, on the same Wi-Fi as the controller.
- A Cloud API app at developer.dji.com (Apps → Create App → type "Cloud API"). You need its App ID, App Key and License.
- Allow ports 8080, 1883 and 8083 through the computer's firewall.
- Find the computer's LAN IP (`ip a` on Linux, `ipconfig` on Windows), e.g. `192.168.1.50`.

## 2. Optional: pre-fill the page

Open `web/index.html` and fill in the `DEFAULTS` block near the top of the script
(App ID, Key, License, broker address). Otherwise you type them on the controller once; the page remembers them.

## 3. Start everything

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f watcher
```

You should see `Connected to broker:1883`.

## 4. Connect the controller

1. On the RC Pro, open DJI Pilot 2.
2. Main page → **Cloud Service** → **Open Platforms** (bottom right).
3. Enter `http://192.168.1.50:8080` (your computer's IP) and tap **Connect**.
4. The page should say "Running inside DJI Pilot 2". Fill in:
   - App ID / App Key / License
   - Address: `tcp://192.168.1.50:1883`
   - Username `pilot`, password `pilot123`
5. Tap **Connect**. Both lights should turn green.
6. Press back and use Pilot 2 normally. Don't tap exit in Cloud Service.

## 5. What success looks like

Power on the aircraft. The watcher log should show:

```
Controller <RC_SN> online, aircraft: <AIRCRAFT_SN>
Sent update_topo reply to <RC_SN>
AIRCRAFT <AIRCRAFT_SN>  lat=...  lon=...  height=...m  rel_alt=...m  heading=...
```

Position lines arrive about every 2 seconds (DJI pushes OSD at 0.5 Hz).
Lines marked `CONTROLLER` are the controller's own GPS, not the drone.

## 6. Switch to your partner's broker

1. On the controller page, change **Address**, **Username**, **Password** to the partner's details and tap **Connect** again.
   DJI documents `tcp://` and `ws://` addresses. If the partner gives `mqtts://` or `wss://`, try it, and see Troubleshooting if it fails.
2. To watch their broker from here, edit `.env`:
   ```
   WATCH_HOST=partner-broker.example.com
   WATCH_PORT=1883
   WATCH_TLS=false        # true for TLS ports such as 8883
   WATCH_USER=...
   WATCH_PASS=...
   REPLY_TOPO=true        # false if the partner's backend already replies
   ```
   then `docker compose up -d watcher`.
3. You can stop the local broker: `docker compose stop broker`.

The controller then needs internet during flights (hotspot or cellular), since the partner's broker isn't on your LAN.

## Troubleshooting

- **Page shows "Preview mode" on the controller**: it wasn't opened through Open Platforms. The bridge only exists there.
- **Licence check fails**: re-copy the three values; make sure the controller has internet the first time.
- **Broker light stays red**: wrong address/port/credentials, or firewall. Check `docker compose logs broker` for the login attempt. Anonymous logins are refused on purpose (DJI requires a password).
- **Connected but no position lines**: aircraft off or not linked; or nobody answers the online handshake (keep `REPLY_TOPO=true` unless the partner's backend replies).
- **Partner broker fails over TLS**: DJI's docs mention GoDaddy-issued certificates for Pilot 2; a certificate from another authority may be rejected. Ask the partner for a plain `tcp://` or `ws://` port for testing to isolate it.

## Notes

- The page stores the broker password in Pilot 2's browser storage. Don't host it publicly, and ask the partner for credentials limited to your devices' topics.
- Pin your Pilot 2 version once this works, and retest before updating.
