#!/usr/bin/env bash
#
# verify_setup.sh — confirm the workshop environment is ready.
#
# Runs each environment check in order. Exits on the first failure with a
# message pointing at the tool that isn't available. Prints "Success" only
# when every check passes.

set -euo pipefail

echo "Checking Python + dependencies (paho-mqtt, psycopg2, python-dotenv)..."
python3 -c "import paho.mqtt.client, psycopg2, dotenv" \
  || { echo "FAILED: Python dependencies missing"; exit 1; }

echo "Checking Mosquitto MQTT client..."
# Note: `mosquitto_sub --version` exits non-zero, so check for the binary itself.
command -v mosquitto_sub >/dev/null \
  || { echo "FAILED: mosquitto_sub not found"; exit 1; }

echo "Checking PostgreSQL client (psql)..."
psql --version >/dev/null \
  || { echo "FAILED: psql not found"; exit 1; }

echo "Checking Grafana (port 3000)..."
curl -sf http://localhost:3000/api/health >/dev/null \
  || { echo "FAILED: Grafana not responding on port 3000"; exit 1; }

echo "Success"
