CREATE TABLE IF NOT EXISTS reading_records (
    reading_id UUID PRIMARY KEY,
    book_id UUID NOT NULL REFERENCES books(book_id),
    reading_status VARCHAR(20) NOT NULL DEFAULT 'completed',
    started_date DATE,
    finished_date DATE,
    rating NUMERIC(2, 1),
    short_review TEXT,
    review TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);