CREATE TABLE book_quotes (

    quote_id UUID PRIMARY KEY,

    book_id UUID NOT NULL
        REFERENCES books(book_id)
        ON DELETE CASCADE,

    page INTEGER,

    quote TEXT NOT NULL,

    my_comment TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);