"""TimescaleDB management and operations."""

import logging
from pathlib import Path

import psycopg2

logger = logging.getLogger(__name__)

# Directory holding the table-creation SQL, executed in order (FK dependencies
# mean tag_meta must be created before tag_history).
SQL_DIR = Path(__file__).resolve().parent / "sql"
SCHEMA_FILES = ["tag_meta.sql", "tag_history.sql"]


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
        """Create tables by executing the SQL files in the sql/ directory."""
        with self.conn.cursor() as cur:
            for filename in SCHEMA_FILES:
                path = SQL_DIR / filename
                cur.execute(path.read_text())
                logger.info(f"Applied schema file: {filename}")
            self.conn.commit()

    def insert_metadata(self, tag_id, tag_name, unit, description):
        """Insert or update tag metadata."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tag_meta (tag_id, tag_name, unit, description)
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
                INSERT INTO tag_history (time, tag_id, value)
                VALUES (%s, %s, %s);
            """, (timestamp, tag_id, value))
            self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Closed TimescaleDB connection")
