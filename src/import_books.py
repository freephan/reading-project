from __future__ import annotations

import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

CSV_FILE = BASE_DIR / "data" / "output" / "books.csv"

DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
    "postgresql+psycopg://",
    "postgresql://",
)


COLUMNS = [
    "book_id",
    "isbn13",
    "isbn10",
    "google_books_id",
    "title",
    "subtitle",
    "authors",
    "translator",
    "publisher",
    "published_date",
    "description",
    "categories",
    "page_count",
    "language_code",
    "cover_url",
    "preview_url",
    "info_url",
    "data_source",
    "created_at",
    "updated_at",
]


INSERT_SQL = """
INSERT INTO books (
    book_id,
    isbn13,
    isbn10,
    google_books_id,
    title,
    subtitle,
    authors,
    translator,
    publisher,
    published_date,
    description,
    categories,
    page_count,
    language_code,
    cover_url,
    preview_url,
    info_url,
    data_source,
    created_at,
    updated_at
)
VALUES (
    %(book_id)s,
    %(isbn13)s,
    %(isbn10)s,
    %(google_books_id)s,
    %(title)s,
    %(subtitle)s,
    %(authors)s,
    %(translator)s,
    %(publisher)s,
    %(published_date)s,
    %(description)s,
    %(categories)s,
    %(page_count)s,
    %(language_code)s,
    %(cover_url)s,
    %(preview_url)s,
    %(info_url)s,
    %(data_source)s,
    %(created_at)s,
    %(updated_at)s
)
ON CONFLICT (book_id) DO NOTHING
"""


def clean_row(row: dict[str, str]) -> dict[str, object]:
    cleaned: dict[str, object] = {}

    for column in COLUMNS:
        value = row.get(column, "").strip()

        if value == "":
            cleaned[column] = None
        else:
            cleaned[column] = value

    page_count = cleaned.get("page_count")

    if page_count is not None:
        try:
            cleaned["page_count"] = int(str(page_count))
        except ValueError:
            cleaned["page_count"] = None

    return cleaned


def main() -> None:
    if not DATABASE_URL:
        print("[실패] .env에 DATABASE_URL이 없습니다.")
        return

    if not CSV_FILE.exists():
        print(f"[실패] CSV 파일이 없습니다: {CSV_FILE}")
        return

    with CSV_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        print("[종료] 가져올 책이 없습니다.")
        return

    inserted_count = 0

    try:
        with psycopg.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                for row in rows:
                    cleaned_row = clean_row(row)

                    cursor.execute(
                        INSERT_SQL,
                        cleaned_row,
                    )

                    inserted_count += cursor.rowcount

            connection.commit()

    except Exception as error:
        print(f"[실패] 데이터베이스 저장 오류: {error}")
        return

    print(f"[완료] 데이터베이스 저장: {inserted_count}건")


if __name__ == "__main__":
    main()