#!/bin/sh
# Writes config.js from env variables so the page gets its defaults without editing index.html.
set -e

esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

mkdir -p /usr/share/nginx/config
cat > /usr/share/nginx/config/config.js <<JS
window.PAGE_CONFIG = {
  appId: "$(esc "$DJI_APP_ID")",
  appKey: "$(esc "$DJI_APP_KEY")",
  license: "$(esc "$DJI_LICENSE")",
  host: "$(esc "$BROKER_HOST")",
  user: "$(esc "$BROKER_USER")",
  pass: "$(esc "$BROKER_PASS")"
};
JS
