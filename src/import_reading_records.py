from __future__ import annotations

import csv
import os
import uuid
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = BASE_DIR / "data" / "input" / "reading_records.csv"

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
    "postgresql+psycopg://",
    "postgresql://",
)


INSERT_SQL = """
INSERT INTO reading_records (
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
SELECT
    %(reading_id)s,
    book_id,
    %(reading_status)s,
    %(started_date)s,
    %(finished_date)s,
    %(rating)s,
    %(short_review)s,
    %(review)s,
    %(created_at)s,
    %(updated_at)s
FROM books
WHERE isbn13 = %(isbn13)s
ON CONFLICT (reading_id) DO NOTHING
"""


def empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    return value if value else None


def main() -> None:
    if not DATABASE_URL:
        print("[실패] DATABASE_URL이 없습니다.")
        return

    if not CSV_FILE.exists():
        print(f"[실패] 파일이 없습니다: {CSV_FILE}")
        return

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        print("[종료] 가져올 독서 기록이 없습니다.")
        return

    inserted_count = 0
    failed_count = 0

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            for row in rows:
                isbn13 = empty_to_none(row.get("isbn13"))

                if not isbn13:
                    print("[건너뜀] ISBN이 없습니다.")
                    failed_count += 1
                    continue

                rating = empty_to_none(row.get("rating"))

                data = {
                    "reading_id": str(uuid.uuid4()),
                    "isbn13": isbn13,
                    "reading_status": empty_to_none(
                        row.get("reading_status")
                    ) or "completed",
                    "started_date": empty_to_none(
                        row.get("started_date")
                    ),
                    "finished_date": empty_to_none(
                        row.get("finished_date")
                    ),
                    "rating": float(rating) if rating else None,
                    "short_review": empty_to_none(
                        row.get("short_review")
                    ),
                    "review": empty_to_none(
                        row.get("review")
                    ),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }

                cursor.execute(INSERT_SQL, data)

                if cursor.rowcount == 0:
                    print(f"[실패] books 테이블에 ISBN이 없습니다: {isbn13}")
                    failed_count += 1
                else:
                    inserted_count += 1

        connection.commit()

    print(f"[완료] 저장 {inserted_count}건 / 실패 {failed_count}건")


if __name__ == "__main__":
    main()