-- Metadata describing each sensor tag.
-- Referenced by tag_history.tag_id (see tag_history.sql).
CREATE TABLE IF NOT EXISTS tag_meta (
    tag_id VARCHAR(255) PRIMARY KEY,
    tag_name VARCHAR(255) NOT NULL,
    unit VARCHAR(100),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
