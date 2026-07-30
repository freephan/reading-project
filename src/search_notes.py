from __future__ import annotations

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace(
    "postgresql+psycopg://",
    "postgresql://",
)


def main():

    isbn = input("ISBN13 : ").strip()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    b.title,
                    n.page,
                    n.note
                FROM book_notes n
                JOIN books b
                  ON n.book_id=b.book_id
                WHERE b.isbn13=%s
                ORDER BY n.page
            """, (isbn,))

            rows = cur.fetchall()

            if not rows:
                print("메모가 없습니다.")
                return

            print(f"\n=== {rows[0][0]} ===\n")

            for _, page, note in rows:

                print(f"[p.{page}]")
                print(note)
                print("-" * 60)


if __name__ == "__main__":
    main()