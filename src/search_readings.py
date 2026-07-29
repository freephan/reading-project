from __future__ import annotations

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace(
    "postgresql+psycopg://",
    "postgresql://",
)

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:

        cur.execute("""
        SELECT
            b.title,
            r.finished_date,
            r.rating,
            r.short_review
        FROM reading_records r
        JOIN books b
          ON r.book_id = b.book_id
        ORDER BY r.finished_date DESC NULLS LAST
        """)

        rows = cur.fetchall()

for title, finished, rating, review in rows:
    print("-" * 60)
    print(title)
    print(f"완독일 : {finished}")
    print(f"평점   : {rating}")
    print(f"한줄평 : {review}")