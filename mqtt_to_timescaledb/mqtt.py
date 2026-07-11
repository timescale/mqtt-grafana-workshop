"""MQTT reader for sensor data."""

import json
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


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
            client.subscribe("UNS/manufacturing/#")
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 6:
                logger.warning(f"Invalid topic format: {msg.topic}")
                return

            tag_name = topic_parts[-1]
            plant = topic_parts[2] if len(topic_parts) > 2 else "unknown"
            area = topic_parts[3] if len(topic_parts) > 3 else "unknown"
            machine = topic_parts[4] if len(topic_parts) > 4 else "unknown"

            tag_id = f"{plant}/{area}/{machine}/{tag_name}"

            payload = json.loads(msg.payload.decode('utf-8'))

            timestamp = payload.get('timestamp')
            unit = payload.get('unit')
            description = payload.get('description')
            value = payload.get('value')

            if timestamp and value is not None:
                self.db_manager.insert_metadata(tag_id, tag_name, unit, description)
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
