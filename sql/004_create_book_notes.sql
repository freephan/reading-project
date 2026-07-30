CREATE TABLE book_notes (

    note_id UUID PRIMARY KEY,

    book_id UUID NOT NULL
        REFERENCES books(book_id)
        ON DELETE CASCADE,

    page INTEGER,

    note TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);