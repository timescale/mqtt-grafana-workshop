#!/usr/bin/env python3
"""Entry point for MQTT to TimescaleDB application."""

import logging
import signal
import threading

from .config import load_config, build_connection_string
from .database import TimescaleDBManager
from .mqtt import MQTTReader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    config = load_config()

    connection_string = build_connection_string(config['database'])
    db_manager = TimescaleDBManager(connection_string)

    mqtt_reader = MQTTReader(
        config['mqtt']['host'],
        config['mqtt']['port'],
        db_manager
    )

    shutdown = threading.Event()

    def signal_handler(sig, frame):
        # Keep the handler minimal: just signal the main thread to stop.
        # Doing cleanup here can deadlock if the signal arrives mid-callback.
        logger.info("Shutdown signal received")
        shutdown.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting MQTT to TimescaleDB reader")
    mqtt_reader.start()

    try:
        shutdown.wait()
    finally:
        logger.info("Shutting down...")
        mqtt_reader.stop()
        db_manager.close()


if __name__ == '__main__':
    main()
