from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from database import engine


BASE_DIR = Path(__file__).resolve().parent.parent
BOOKS_CSV_FILE = BASE_DIR / "data" / "output" / "books.csv"


UPSERT_BOOK_SQL = text(
    """
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
        CAST(:book_id AS UUID),
        NULLIF(:isbn13, ''),
        NULLIF(:isbn10, ''),
        NULLIF(:google_books_id, ''),
        :title,
        NULLIF(:subtitle, ''),
        NULLIF(:authors, ''),
        NULLIF(:translator, ''),
        NULLIF(:publisher, ''),
        NULLIF(:published_date, ''),
        NULLIF(:description, ''),
        NULLIF(:categories, ''),
        :page_count,
        NULLIF(:language_code, ''),
        NULLIF(:cover_url, ''),
        NULLIF(:preview_url, ''),
        NULLIF(:info_url, ''),
        NULLIF(:data_source, ''),
        CAST(:created_at AS TIMESTAMPTZ),
        CAST(:updated_at AS TIMESTAMPTZ)
    )
    ON CONFLICT (isbn13)
    DO UPDATE SET
        isbn10 = EXCLUDED.isbn10,
        google_books_id = EXCLUDED.google_books_id,
        title = EXCLUDED.title,
        subtitle = EXCLUDED.subtitle,
        authors = EXCLUDED.authors,
        translator = EXCLUDED.translator,
        publisher = EXCLUDED.publisher,
        published_date = EXCLUDED.published_date,
        description = EXCLUDED.description,
        categories = EXCLUDED.categories,
        page_count = EXCLUDED.page_count,
        language_code = EXCLUDED.language_code,
        cover_url = EXCLUDED.cover_url,
        preview_url = EXCLUDED.preview_url,
        info_url = EXCLUDED.info_url,
        data_source = EXCLUDED.data_source,
        updated_at = CURRENT_TIMESTAMP
    RETURNING
        book_id,
        title,
        (xmax = 0) AS inserted
    """
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def clean_page_count(value: Any) -> int | None:
    cleaned_value = clean_text(value)

    if not cleaned_value:
        return None

    try:
        return int(float(cleaned_value))
    except ValueError:
        return None


def clean_datetime(value: Any) -> str:
    cleaned_value = clean_text(value)

    if cleaned_value:
        return cleaned_value

    return datetime.now(timezone.utc).isoformat()


def prepare_book_row(row: dict[str, Any]) -> dict[str, Any]:
    isbn13 = clean_text(row.get("isbn13"))
    title = clean_text(row.get("title"))

    if not isbn13:
        raise ValueError("isbn13이 비어 있습니다.")

    if not title:
        raise ValueError("title이 비어 있습니다.")

    return {
        "book_id": clean_text(row.get("book_id")),
        "isbn13": isbn13,
        "isbn10": clean_text(row.get("isbn10")),
        "google_books_id": clean_text(
            row.get("google_books_id")
        ),
        "title": title,
        "subtitle": clean_text(row.get("subtitle")),
        "authors": clean_text(row.get("authors")),
        "translator": clean_text(row.get("translator")),
        "publisher": clean_text(row.get("publisher")),
        "published_date": clean_text(
            row.get("published_date")
        ),
        "description": clean_text(row.get("description")),
        "categories": clean_text(row.get("categories")),
        "page_count": clean_page_count(
            row.get("page_count")
        ),
        "language_code": clean_text(
            row.get("language_code")
        ),
        "cover_url": clean_text(row.get("cover_url")),
        "preview_url": clean_text(row.get("preview_url")),
        "info_url": clean_text(row.get("info_url")),
        "data_source": clean_text(
            row.get("data_source")
        ),
        "created_at": clean_datetime(
            row.get("created_at")
        ),
        "updated_at": clean_datetime(
            row.get("updated_at")
        ),
    }


def read_books_csv(
    csv_file: Path,
) -> list[dict[str, Any]]:
    if not csv_file.exists():
        raise FileNotFoundError(
            f"books.csv 파일을 찾을 수 없습니다: {csv_file}"
        )

    rows: list[dict[str, Any]] = []

    with csv_file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        required_columns = {
            "book_id",
            "isbn13",
            "title",
        }

        actual_columns = set(reader.fieldnames or [])
        missing_columns = required_columns - actual_columns

        if missing_columns:
            missing_text = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                f"books.csv 필수 컬럼이 없습니다: {missing_text}"
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            try:
                prepared_row = prepare_book_row(row)
                rows.append(prepared_row)

            except ValueError as error:
                print(
                    f"[건너뜀] CSV {row_number}행: {error}"
                )

    return rows


def import_books(
    rows: list[dict[str, Any]],
) -> tuple[int, int, int]:
    inserted_count = 0
    updated_count = 0
    failed_count = 0

    with engine.begin() as connection:
        for index, row in enumerate(rows, start=1):
            try:
                result = connection.execute(
                    UPSERT_BOOK_SQL,
                    row,
                ).one()

                title = result.title
                inserted = result.inserted

                if inserted:
                    inserted_count += 1
                    action = "추가"
                else:
                    updated_count += 1
                    action = "갱신"

                print(
                    f"[{index}/{len(rows)}] "
                    f"{action}: {title}"
                )

            except Exception as error:
                failed_count += 1

                print(
                    f"[{index}/{len(rows)}] "
                    f"실패: {row.get('title', '')}"
                )
                print(f"  원인: {error}")

    return (
        inserted_count,
        updated_count,
        failed_count,
    )


def main() -> None:
    try:
        rows = read_books_csv(BOOKS_CSV_FILE)
    except (FileNotFoundError, ValueError) as error:
        print(f"[실패] {error}")
        return

    if not rows:
        print("[종료] 가져올 책이 없습니다.")
        return

    print(f"가져올 책: {len(rows)}권")
    print()

    inserted, updated, failed = import_books(rows)

    print()
    print("DB 적재 완료")
    print(f"새로 추가: {inserted}권")
    print(f"기존 정보 갱신: {updated}권")
    print(f"실패: {failed}권")


if __name__ == "__main__":
    main()