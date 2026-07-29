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
                    r.reading_id,
                    b.title,
                    r.rating,
                    r.short_review
                FROM reading_records r
                JOIN books b
                  ON r.book_id = b.book_id
                WHERE b.isbn13=%s
            """, (isbn,))

            row = cur.fetchone()

            if row is None:
                print("독서기록이 없습니다.")
                return

            reading_id, title, rating, short_review = row

            print(f"\n책 : {title}")
            print(f"현재 평점 : {rating}")
            print(f"현재 한줄평 : {short_review}")

            new_rating = input("새 평점 : ").strip()
            new_review = input("새 한줄평 : ").strip()

            cur.execute("""
                UPDATE reading_records
                SET
                    rating=%s,
                    short_review=%s,
                    updated_at=NOW()
                WHERE reading_id=%s
            """,
            (
                float(new_rating),
                new_review,
                reading_id,
            ))

        conn.commit()

    print("수정 완료")


if __name__ == "__main__":
    main()