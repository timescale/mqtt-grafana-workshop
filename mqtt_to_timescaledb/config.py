"""Configuration and environment loading."""

import os
from dotenv import load_dotenv


def load_config():
    """Load configuration from environment variables."""
    load_dotenv('tiger-cloud-workshop_db-credentials.env')

    return {
        'mqtt': {
            'host': os.getenv('MQTT_HOST', '54.160.236.103'),
            'port': int(os.getenv('MQTT_PORT', '1883')),
            'subscribe_topic': 'UNS/manufacturing/#'
        },
        'database': {
            'host': os.getenv('TIMESCALEDB_HOST', 'localhost'),
            'port': os.getenv('TIMESCALEDB_PORT', '5432'),
            'name': os.getenv('TIMESCALEDB_NAME', 'sensor_data'),
            'user': os.getenv('TIMESCALEDB_USER', 'postgres'),
            'password': os.getenv('TIMESCALEDB_PASSWORD', 'password'),
        }
    }


def build_connection_string(db_config):
    """Build PostgreSQL connection string from config dict."""
    return (
        f"host={db_config['host']} port={db_config['port']} "
        f"dbname={db_config['name']} user={db_config['user']} "
        f"password={db_config['password']}"
    )
