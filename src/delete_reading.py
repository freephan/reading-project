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

    isbn = input("삭제할 책 ISBN13 : ").strip()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    r.reading_id,
                    b.title
                FROM reading_records r
                JOIN books b
                  ON r.book_id = b.book_id
                WHERE b.isbn13 = %s
            """, (isbn,))

            row = cur.fetchone()

            if row is None:
                print("독서기록이 없습니다.")
                return

            reading_id, title = row

            print(f"\n삭제 대상 : {title}")

            confirm = input("정말 삭제하시겠습니까? (y/N) : ").strip().lower()

            if confirm != "y":
                print("취소되었습니다.")
                return

            cur.execute("""
                DELETE FROM reading_records
                WHERE reading_id = %s
            """, (reading_id,))

        conn.commit()

    print("삭제 완료")


if __name__ == "__main__":
    main()