"""Configuration and environment loading."""

import os
from dotenv import load_dotenv


def load_config():
    """Load configuration from environment variables."""
    load_dotenv()

    return {
        'mqtt': {
            'host': os.getenv('MQTT_HOST', '54.160.239.103'),
            'port': int(os.getenv('MQTT_PORT', '1883')),
            'subscribe_topic': 'UNS/manufacturing/#'
        },
        'database': {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'name': os.getenv('PGDATABASE', 'sensor_data'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', 'password'),
        }
    }


def build_connection_string(db_config):
    """Build PostgreSQL connection string from config dict."""
    return (
        f"host={db_config['host']} port={db_config['port']} "
        f"dbname={db_config['name']} user={db_config['user']} "
        f"password={db_config['password']}"
    )
