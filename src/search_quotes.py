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
                    q.page,
                    q.quote,
                    q.my_comment
                FROM book_quotes q
                JOIN books b
                  ON q.book_id = b.book_id
                WHERE b.isbn13 = %s
                ORDER BY q.page
            """, (isbn,))

            rows = cur.fetchall()

            if not rows:
                print("저장된 문장이 없습니다.")
                return

            print(f"\n=== {rows[0][0]} ===\n")

            for _, page, quote, comment in rows:
                print(f"[p.{page}]")
                print(quote)

                if comment:
                    print(f"\n내 생각 : {comment}")

                print("-" * 60)


if __name__ == "__main__":
    main()