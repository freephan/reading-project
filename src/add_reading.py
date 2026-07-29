from __future__ import annotations

import os
import uuid
from datetime import datetime

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

            cur.execute(
                """
                SELECT book_id, title
                FROM books
                WHERE isbn13=%s
                """,
                (isbn,),
            )

            book = cur.fetchone()

            if not book:
                print("책이 없습니다.")
                return

            book_id, title = book

            print(f"\n책 : {title}")

            started = input("읽기 시작일(YYYY-MM-DD) : ").strip()
            finished = input("완독일(YYYY-MM-DD) : ").strip()
            rating = input("평점(0~5) : ").strip()
            short_review = input("한줄평 : ").strip()

            print("\n독후감 입력")
            print("빈 줄만 입력하면 종료")

            lines = []

            while True:

                line = input()

                if line == "":
                    break

                lines.append(line)

            review = "\n".join(lines)

            cur.execute(
                """
                INSERT INTO reading_records(
                    reading_id,
                    book_id,
                    reading_status,
                    started_date,
                    finished_date,
                    rating,
                    short_review,
                    review,
                    created_at,
                    updated_at
                )
                VALUES(
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    str(uuid.uuid4()),
                    book_id,
                    "completed",
                    started,
                    finished,
                    float(rating),
                    short_review,
                    review,
                    datetime.now(),
                    datetime.now(),
                ),
            )

        conn.commit()

    print("\n저장 완료")


if __name__ == "__main__":
    main()