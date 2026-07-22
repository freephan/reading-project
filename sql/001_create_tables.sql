CREATE EXTENSION IF NOT EXISTS pgcrypto;


CREATE TABLE IF NOT EXISTS books (
    book_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    isbn13 VARCHAR(13) UNIQUE,
    isbn10 VARCHAR(10),

    google_books_id VARCHAR(100),

    title TEXT NOT NULL,
    subtitle TEXT,

    authors TEXT,
    translator TEXT,
    publisher TEXT,
    published_date VARCHAR(20),

    description TEXT,
    categories TEXT,

    page_count INTEGER,
    language_code VARCHAR(10),

    cover_url TEXT,
    preview_url TEXT,
    info_url TEXT,

    data_source VARCHAR(50),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS reading_history (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    book_id UUID NOT NULL
        REFERENCES books(book_id)
        ON DELETE CASCADE,

    reading_status VARCHAR(20) NOT NULL DEFAULT 'want_to_read',

    started_date DATE,
    finished_date DATE,

    rating NUMERIC(2, 1),

    one_line_review TEXT,
    review TEXT,
    good_points TEXT,
    bad_points TEXT,
    summary TEXT,

    is_owned BOOLEAN NOT NULL DEFAULT FALSE,
    acquisition_type VARCHAR(30),
    library_name TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT rating_range
        CHECK (rating IS NULL OR rating BETWEEN 0 AND 5),

    CONSTRAINT finished_after_started
        CHECK (
            finished_date IS NULL
            OR started_date IS NULL
            OR finished_date >= started_date
        ),

    CONSTRAINT valid_reading_status
        CHECK (
            reading_status IN (
                'want_to_read',
                'reading',
                'completed',
                'paused',
                'abandoned',
                'rereading'
            )
        )
);


CREATE TABLE IF NOT EXISTS quotes (
    quote_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    reading_id UUID NOT NULL
        REFERENCES reading_history(reading_id)
        ON DELETE CASCADE,

    quote_text TEXT NOT NULL,
    page_number INTEGER,
    memo TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_page_number
        CHECK (
            page_number IS NULL
            OR page_number > 0
        )
);


CREATE TABLE IF NOT EXISTS tags (
    tag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tag_name VARCHAR(100) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS book_tags (
    book_id UUID NOT NULL
        REFERENCES books(book_id)
        ON DELETE CASCADE,

    tag_id UUID NOT NULL
        REFERENCES tags(tag_id)
        ON DELETE CASCADE,

    PRIMARY KEY (book_id, tag_id)
);


CREATE INDEX IF NOT EXISTS idx_books_title
    ON books(title);


CREATE INDEX IF NOT EXISTS idx_books_isbn13
    ON books(isbn13);


CREATE INDEX IF NOT EXISTS idx_reading_history_book_id
    ON reading_history(book_id);


CREATE INDEX IF NOT EXISTS idx_reading_history_status
    ON reading_history(reading_status);


CREATE INDEX IF NOT EXISTS idx_reading_history_finished_date
    ON reading_history(finished_date);