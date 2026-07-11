"""TimescaleDB management and operations."""

import logging
import psycopg2

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

            cur.execute("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    time TIMESTAMP NOT NULL,
                    tag_id VARCHAR(255) NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    FOREIGN KEY (tag_id) REFERENCES tag_metadata(tag_id)
                );
            """)

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
