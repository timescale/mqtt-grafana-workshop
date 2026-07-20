-- Time-series sensor readings, stored as a TimescaleDB hypertable.
-- Depends on tag_meta (run tag_meta.sql first).
-- The hypertable is created directly in the CREATE TABLE statement via the
-- tsdb.* storage options, as recommended by TigerData.
CREATE TABLE IF NOT EXISTS tag_history (
    time TIMESTAMPTZ NOT NULL,
    tag_id VARCHAR(255) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    FOREIGN KEY (tag_id) REFERENCES tag_meta(tag_id)
) WITH (
    tsdb.hypertable,
    tsdb.partition_column = 'time'
);
