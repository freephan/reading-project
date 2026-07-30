from __future__ import annotations

import os
import uuid

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
                SELECT book_id, title
                FROM books
                WHERE isbn13=%s
            """, (isbn,))

            book = cur.fetchone()

            if book is None:
                print("책을 찾을 수 없습니다.")
                return

            book_id, title = book

            print(f"\n책 : {title}")

            page = input("페이지 : ").strip()

            print("\n인용문 입력")
            quote = input("> ")

            print("\n내 생각")
            comment = input("> ")

            cur.execute("""
                INSERT INTO book_quotes(
                    quote_id,
                    book_id,
                    page,
                    quote,
                    my_comment
                )
                VALUES(%s,%s,%s,%s,%s)
            """,
            (
                str(uuid.uuid4()),
                book_id,
                int(page),
                quote,
                comment
            ))

        conn.commit()

    print("저장 완료")


if __name__ == "__main__":
    main()