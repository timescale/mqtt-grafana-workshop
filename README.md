# MQTT to TimescaleDB Workshop

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/timescale/mqtt-grafana-workshop)

A practical workshop for streaming manufacturing sensor data from MQTT to TimescaleDB on Tiger Cloud.

## 1. Overview

This project demonstrates a real-time data pipeline:
1. **MQTT Broker** — Publishes sensor data from manufacturing equipment
2. **Python Application** — Subscribes to MQTT topics and processes messages
3. **TimescaleDB** — Stores time-series sensor readings and metadata

The architecture separates concerns into modular components:
- `config.py` — Environment configuration and secrets
- `database.py` — Database operations and schema management
- `mqtt.py` — MQTT subscription and message handling
- `main.py` — Application lifecycle and signal handling

## 2. Prerequisites (include in codespace)

- Python 3.8+
- `mosquitto-clients` (for MQTT testing)
- `psql` (PostgreSQL client, for database testing)
- TimescaleDB connection details (host, port, credentials)
- MQTT broker access

## 3. Installation

1. **Verify your environment is set up correctly:**

   The devcontainer installs everything automatically, so start by confirming
   each tool is available. Run the verification script:

   ```bash
   ./verify_setup.sh
   ```

   It prints `Success` when everything is ready. The script runs these checks:

   - **Python + dependencies** — `paho-mqtt`, `psycopg2`, `python-dotenv` import cleanly
   - **Mosquitto MQTT client** — `mosquitto_sub` is installed
   - **PostgreSQL client** — `psql` is installed
   - **Grafana** — responding on port 3000

   If any check fails, the script stops and prints which tool is missing.


2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Fill in your Tiger Cloud credentials:**
   ```bash
   # Edit .env with:
   PGPASSWORD=your-password
   PGUSER=your-username
   PGDATABASE=sensor_data
   PGHOST=your-timescale-host
   PGPORT=5432
   
   # Optional: Override default MQTT broker
   MQTT_HOST=your-mqtt-host
   MQTT_PORT=1883
   ```

## 4. How to Test MQTT Stream with Mosquitto

### a. Subscribe to Test Topics

Open a terminal and subscribe to the manufacturing sensor topics:

```bash
# Subscribe to all manufacturing sensors
mosquitto_sub -h 54.160.239.103 -p 1883 -t "UNS/manufacturing/#" -v
```


## 5. How to Connect and Test Tiger Cloud with psql

### a. Connect to TimescaleDB

Because the credentials file uses the standard `PG*` variable names, you can
load it into your shell and run `psql` with no arguments — libpq reads the
connection details (including the password) straight from the environment:

```bash
# Export everything in the credentials file, then connect
set -a
source .env
set +a

psql
```

Or, you can manuallly enter the connection details with the following command:

```bash
# Connect to your TimescaleDB instance
psql -h your-timescale-host -U your-username -d sensor_data -W

# Enter your password when prompted
```

### b. Create/Verify Tables and Schema

#### Load the schema from the SQL files

Instead of letting the Python application create the tables on startup, you can
load them manually. Run the files in order — `tag_meta.sql` first, since
`tag_history` has a foreign key to it. Assuming your credentials are already
exported (see above), `psql` picks up the connection details automatically:

```bash
psql -f mqtt_to_timescaledb/sql/tag_meta.sql
psql -f mqtt_to_timescaledb/sql/tag_history.sql
```

#### Verify the tables

Sign in to an interactive `psql` session:

```bash
psql
```

Then run the verification commands:

```sql
-- List all tables
\dt

-- View table structure
\d tag_meta
\d tag_history

-- Check if tag_history is a hypertable
SELECT * FROM timescaledb_information.hypertables;
```

When you're done, sign out of the session:

```sql
\q
```

## 6. How to Run the Python Code

### a. Quick Start

```bash
python mqtt_to_timescaledb.py
```

The application will:
1. Load configuration from environment variables
2. Connect to TimescaleDB and initialize tables/hypertable
3. Connect to MQTT broker and subscribe to `UNS/manufacturing/#`
4. Process incoming messages and store readings in the database
5. Log all activities to console

### b. Graceful Shutdown

Press `Ctrl+C` to trigger graceful shutdown:
- Stops MQTT subscription
- Closes database connection
- Logs shutdown information

> **Running in a browser-based Codespace?** `Ctrl+C` may be intercepted by the
> browser and never reach the application. If pressing `Ctrl+C` does nothing,
> the simplest fix is to **kill the terminal** — click the trash-can icon on the
> terminal panel (or run *Terminal: Kill the Active Terminal Instance* from the
> Command Palette) and open a new one. Opening the Codespace in the VS Code
> desktop app also restores normal `Ctrl+C` behavior.

### c. Monitor Logs

The application logs important events:
```
2024-07-11 10:15:23 - mqtt_to_timescaledb - INFO - Connected to TimescaleDB
2024-07-11 10:15:24 - mqtt_to_timescaledb - INFO - Connected to MQTT broker
2024-07-11 10:15:25 - mqtt_to_timescaledb - INFO - Inserted plant1/area1/machine1/bearing_temperature: 65.3 °C at 2024-07-11 10:30:00
```

## 7. Query Sensor Data

Sign in to an interactive `psql` session:

```bash
psql
```

Then run the queries:

```sql
-- Get latest readings for a specific tag
SELECT time, value, tag_id 
FROM tag_history 
WHERE tag_id = 'plant1/area1/machine1/bearing_temperature'
ORDER BY time DESC 
LIMIT 10;

-- Get metadata for all tags
SELECT tag_id, tag_name, unit, description 
FROM tag_meta;
```

When you're done, sign out of the session:

```sql
\q
```

## 8. Visualize in Grafana

Grafana runs alongside the app and is forwarded on port **3000**. Open with the 'open in browser' icon in the PORTS tab. Log in with username `admin` and password `admin` (see `.devcontainer/docker-compose.yml`).

### a. Add the TimescaleDB data source

1. In Grafana, go to **Connections → Data sources → Add data source → PostgreSQL**.
2. Fill in your Tiger Cloud credentials (the same `PG*` values from
   `.env`):
   - **Host**: `PGHOST:PGPORT` (e.g. `your-host:39171`)
   - **Database**: `PGDATABASE` (e.g. `tsdb`)
   - **User**: `PGUSER` (e.g. `tsdbadmin`)
   - **Password**: `PGPASSWORD`
   - **TLS/SSL Mode**: `require`

   > ⚠️ **The Host field must include the port**, joined with a colon
   > (`your-host:39171`). Tiger Cloud does **not** use the default `5432`, and
   > Grafana has no separate port field — if you enter only the hostname the
   > connection will fail. Also set **TLS/SSL Mode** to `require`; Tiger Cloud
   > rejects unencrypted connections.

3. Click **Save & test** — you should see a success message.

### b. Import the dashboard

1. Go to **Dashboards → New → Import**.
2. Click **Upload dashboard JSON file** and choose
   [grafana/sensor_readings_dashboard.json](grafana/sensor_readings_dashboard.json)
   (or paste its contents).
3. When prompted, select the **TimescaleDB** data source you created above.
4. Click **Import**.

The dashboard shows a time-series panel of sensor `value` over time, one series
per `tag_id`, auto-refreshing every 10 seconds. Make sure the Python reader is
running so there's fresh data to plot.

## 9. Troubleshooting

### a. MQTT Connection Issues

```bash
# Test MQTT broker connectivity
mosquitto_sub -h 54.160.239.103 -p 1883 -t '$SYS/#' -W 1

# Check if broker is responding
timeout 2 bash -c 'cat < /dev/null > /dev/tcp/54.160.239.103/1883' && echo "Port is open"
```

### b. TimescaleDB Connection Issues

```bash
# Test connection manually
psql -h your-timescale-host -U your-username -d sensor_data -c "SELECT version();"

# Verify credentials in environment file
cat .env | grep PG
```

### c. No Data Appearing in Database

1. **Verify MQTT messages are being published:**
   ```bash
   mosquitto_sub -h 54.160.239.103 -p 1883 -t "UNS/manufacturing/#" -v
   ```

2. **Check Python application logs** for errors in message parsing

3. **Verify message format** — must include `timestamp` and `value` fields

4. **Check database tables exist:**
   ```sql
   SELECT table_name FROM information_schema.tables WHERE table_schema='public';
   ```

## 10. Workshop Tasks

### a. Level 1: Basic Setup
- [ ] Clone or open in Codespaces
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Configure TimescaleDB credentials
- [ ] Run the Python application
- [ ] Publish a test MQTT message
- [ ] Verify data in database with `psql`

### b. Level 2: Intermediate
- [ ] Subscribe to MQTT topics with `mosquitto_sub`
- [ ] Publish multiple sensor readings with different tags
- [ ] Query data using TimescaleDB time-bucket aggregations
- [ ] Modify the message format and re-run application

### c. Level 3: Advanced
- [ ] Create additional SQL views for common queries
- [ ] Add continuous aggregates in TimescaleDB
- [ ] Modify the Python code to handle additional payload fields
- [ ] Set up monitoring/alerting for sensor thresholds

## 11. Project Structure

```
mqtt_to_timescaledb.py       # Top-level entry point script
mqtt_to_timescaledb/
├── __init__.py              # Package initialization
├── __main__.py              # Module entry point
├── config.py                # Configuration and env loading
├── database.py              # TimescaleDB manager
├── mqtt.py                  # MQTT reader and message handling
├── main.py                  # Application entry point
└── sql/
    ├── tag_meta.sql         # tag_meta table DDL
    └── tag_history.sql      # tag_history hypertable DDL
grafana/
└── sensor_readings_dashboard.json   # Importable Grafana dashboard
```

## 12. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MQTT_HOST` | `54.160.239.103` | MQTT broker hostname |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `PGHOST` | `localhost` | TimescaleDB hostname |
| `PGPORT` | `5432` | TimescaleDB port |
| `PGDATABASE` | `sensor_data` | Database name |
| `PGUSER` | `postgres` | Database user |
| `PGPASSWORD` | `password` | Database password |

## 13. Next Steps

- **Scale the pipeline:** Add message queuing, batch inserts, or compression
- **Visualization:** Connect Grafana or similar tools to TimescaleDB
- **Real-time alerts:** Implement threshold monitoring and notifications
- **Data retention:** Configure TimescaleDB compression and data retention policies
- **Testing:** Add unit tests for message parsing and database operations

## 14. Resources

- [MQTT Protocol](https://mqtt.org/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Mosquitto Tools](https://mosquitto.org/man/)
- [PostgreSQL Client (psql)](https://www.postgresql.org/docs/current/app-psql.html)
- [Tiger Cloud](https://tigerdata.com/)

## 15. Support

For questions or issues:
1. Check the Troubleshooting section above
2. Review application logs for error messages
3. Test MQTT and database connectivity separately
4. Reach out to the workshop facilitator
