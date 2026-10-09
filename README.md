# DJI Pilot 2 telemetry page

A web page that DJI Pilot 2 opens on the remote controller. It checks the DJI licence and
connects Pilot 2 to an MQTT broker, so the aircraft's telemetry is sent there.

For how it works inside, see [ARCHITECTURE.md](ARCHITECTURE.md).

## What you need

- A server with Docker and Docker Compose, reachable from the controller. Port 8080 open.
- A DJI RC with DJI Pilot 2.
- A DJI Cloud API licence: at <https://developer.dji.com> go to **Apps → Create App**, choose
  **Cloud API**, and copy the App ID, App Key and License.
- The address, username and password of the MQTT broker that should receive the data.

## Server setup

1. Copy the settings file:

   ```bash
   cp .env.example .env
   ```

2. Fill in `.env`:

   ```
   DJI_APP_ID=your-app-id
   DJI_APP_KEY=your-app-key
   DJI_LICENSE=your-license

   BROKER_HOST=tcp://broker.example.com:1883
   BROKER_USER=your-broker-username
   BROKER_PASS=your-broker-password
   ```

   These fill in the fields on the page. Anything left empty, the pilot types on the controller.

3. Start the page:

   ```bash
   docker compose up -d web
   ```

To change a value later, edit `.env` and run `docker compose up -d web` again.

Anyone who can open the page can see these values, so only serve it on a network you trust.

## Controller setup

1. Open **DJI Pilot 2**.
2. Tap **Cloud Service → Open Platforms**.
3. Enter `http://<server-ip>:8080` and tap **Connect**.
4. Check the fields are filled in, then tap **Connect** on the page.
5. Wait for both lights to turn green: **DJI licence** and **Broker**.
6. Press back and fly as usual. To stop sending data, open the page and tap **Disconnect**.

The controller remembers the values from the last **Connect**. After changing `.env`, tap
**Forget saved details** on the page to load the new values.

## Testing only

`docker-compose.yml` also has a local test broker and a `watcher` that prints the aircraft's
position. The test broker is only for testing. Do not use it in real use.

1. Put the test broker in `.env`:

   ```
   BROKER_HOST=tcp://<server-ip>:1883
   BROKER_USER=pilot
   BROKER_PASS=pilot123
   ```

2. Open ports 1883 and 8083, then start everything:

   ```bash
   docker compose up -d --build
   docker compose logs -f watcher
   ```

With the aircraft on, the log shows its position about every 2 seconds.

## Replying to `update_topo` on another broker

When Pilot 2 connects, it waits for a reply to its `update_topo` message. If the broker you use
has no back-end that replies, the watcher can do it.

1. Add the broker to `.env`:

   ```
   WATCH_HOST=broker.example.com
   WATCH_PORT=1883
   WATCH_TLS=false        # true for a TLS port, e.g. 8883
   WATCH_USER=your-broker-username
   WATCH_PASS=your-broker-password
   REPLY_TOPO=true
   ```

2. Start only the watcher, without the local test broker:

   ```bash
   docker compose up -d --no-deps watcher
   ```

The watcher must be running whenever the drone flies. It connects over TCP only, not WebSocket.
If the broker's back-end already replies, set `REPLY_TOPO=false` so Pilot 2 doesn't get two replies.

## Troubleshooting

- **Licence light stays red**: re-copy the three licence values, and make sure the controller has internet.
- **Broker light stays red**: wrong address, port, username or password, or a firewall in between.
- **Page says "Preview mode"**: open it from Cloud Service → Open Platforms, not a normal browser.
- **Fields are blank**: open `http://<server-ip>:8080/config.js`. If your values aren't there, check `.env` and run `docker compose up -d web`.
- **Old values still shown**: tap **Forget saved details** on the page.
