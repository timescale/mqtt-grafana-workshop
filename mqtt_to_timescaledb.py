#!/usr/bin/env python3
"""
MQTT to TimescaleDB writer for manufacturing sensor data.

Reads sensor data from MQTT topics and stores:
- Time-series values in a hypertable
- Tag metadata in a separate table
"""

import json
import logging
import os
import signal
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt
import psycopg2
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimescaleDBManager:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.conn = None
        self._connect()
        self._init_tables()

    def _connect(self):
        try:
            self.conn = psycopg2.connect(self.connection_string)
            logger.info("Connected to TimescaleDB")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to TimescaleDB: {e}")
            raise

    def _init_tables(self):
        """Create tables if they don't exist."""
        with self.conn.cursor() as cur:
            # Create metadata table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tag_metadata (
                    tag_id VARCHAR(255) PRIMARY KEY,
                    tag_name VARCHAR(255) NOT NULL,
                    unit VARCHAR(100),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            logger.info("tag_metadata table created or already exists")

            # Create hypertable for time-series values
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    time TIMESTAMP NOT NULL,
                    tag_id VARCHAR(255) NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    FOREIGN KEY (tag_id) REFERENCES tag_metadata(tag_id)
                );
            """)

            # Convert to hypertable if not already
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'sensor_readings'
                    AND EXISTS (
                        SELECT 1 FROM timescaledb_information.hypertables
                        WHERE hypertable_name = 'sensor_readings'
                    )
                ) AS is_hypertable;
            """)
            is_hypertable = cur.fetchone()[0]

            if not is_hypertable:
                try:
                    cur.execute("""
                        SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);
                    """)
                    logger.info("Created hypertable: sensor_readings")
                except psycopg2.Error as e:
                    if "already" not in str(e):
                        logger.warning(f"Hypertable creation: {e}")

            self.conn.commit()

    def insert_metadata(self, tag_id, tag_name, unit, description):
        """Insert or update tag metadata."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tag_metadata (tag_id, tag_name, unit, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tag_id) DO UPDATE SET
                    tag_name = EXCLUDED.tag_name,
                    unit = EXCLUDED.unit,
                    description = EXCLUDED.description,
                    updated_at = CURRENT_TIMESTAMP;
            """, (tag_id, tag_name, unit, description))
            self.conn.commit()

    def insert_reading(self, timestamp, tag_id, value):
        """Insert a sensor reading."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sensor_readings (time, tag_id, value)
                VALUES (%s, %s, %s);
            """, (timestamp, tag_id, value))
            self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Closed TimescaleDB connection")


class MQTTReader:
    def __init__(self, broker_host, broker_port, db_manager):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.db_manager = db_manager
        self.client = mqtt.Client()
        self.running = True

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Subscribe to all sensor topics
            client.subscribe("UNS/manufacturing/#")
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            # Parse topic: UNS/manufacturing/plant1/area1/machine1/bearing_temperature
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 6:
                logger.warning(f"Invalid topic format: {msg.topic}")
                return

            tag_name = topic_parts[-1]
            plant = topic_parts[2] if len(topic_parts) > 2 else "unknown"
            area = topic_parts[3] if len(topic_parts) > 3 else "unknown"
            machine = topic_parts[4] if len(topic_parts) > 4 else "unknown"

            # Create unique tag_id from path
            tag_id = f"{plant}/{area}/{machine}/{tag_name}"

            # Parse payload
            payload = json.loads(msg.payload.decode('utf-8'))

            timestamp = payload.get('timestamp')
            unit = payload.get('unit')
            description = payload.get('description')
            value = payload.get('value')

            if timestamp and value is not None:
                # Insert or update metadata
                self.db_manager.insert_metadata(tag_id, tag_name, unit, description)

                # Insert reading
                self.db_manager.insert_reading(timestamp, tag_id, value)
                logger.info(f"Inserted {tag_id}: {value} {unit} at {timestamp}")
            else:
                logger.warning(f"Missing timestamp or value in payload: {payload}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected disconnection (code {rc})")

    def connect(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            raise

    def start(self):
        """Start reading from MQTT broker."""
        self.connect()
        self.client.loop_start()

    def stop(self):
        """Stop reading from MQTT broker."""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Stopped MQTT reader")


def main():
    # MQTT Configuration
    mqtt_host = '54.160.236.103'
    mqtt_port = 1883

    # Load environment variables from tiger-cloud-workshop_db-credentials.env
    load_dotenv('tiger-cloud-workshop_db-credentials.env')

    # Read database configuration from environment
    db_host = os.getenv('TIMESCALEDB_HOST', 'localhost')
    db_port = os.getenv('TIMESCALEDB_PORT', '5432')
    db_name = os.getenv('TIMESCALEDB_NAME', 'sensor_data')
    db_user = os.getenv('TIMESCALEDB_USER', 'postgres')
    db_password = os.getenv('TIMESCALEDB_PASSWORD', 'password')

    # Build connection string
    connection_string = (
        f"host={db_host} port={db_port} database={db_name} "
        f"user={db_user} password={db_password}"
    )

    # Initialize database manager
    db_manager = TimescaleDBManager(connection_string)

    # Initialize MQTT reader
    mqtt_reader = MQTTReader(mqtt_host, mqtt_port, db_manager)

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        mqtt_reader.stop()
        db_manager.close()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start reading
    logger.info("Starting MQTT to TimescaleDB reader")
    mqtt_reader.start()

    # Keep the program running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        mqtt_reader.stop()
        db_manager.close()


if __name__ == '__main__':
    main()
