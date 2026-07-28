from __future__ import annotations

import csv
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")

INPUT_FILE = BASE_DIR / "data" / "input" / "isbn_input.csv"
OUTPUT_FILE = BASE_DIR / "data" / "output" / "books.csv"
ERROR_FILE = BASE_DIR / "data" / "output" / "books_errors.csv"

API_URL = "https://www.googleapis.com/books/v1/volumes"

BOOK_COLUMNS = [
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

ERROR_COLUMNS = [
    "isbn",
    "error_type",
    "message",
]


def normalize_isbn(value: str) -> str:
    """ISBN에서 숫자와 ISBN-10의 X만 남긴다."""
    return re.sub(
        r"[^0-9Xx]",
        "",
        value or "",
    ).upper()


def read_isbns() -> tuple[list[str], list[dict[str, str]]]:
    """isbn_input.csv에서 ISBN 목록을 읽는다."""
    isbns: list[str] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"입력 파일이 없습니다: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or "isbn13" not in reader.fieldnames:
            raise ValueError(
                "isbn_input.csv에 isbn13 컬럼이 필요합니다."
            )

        for row_number, row in enumerate(reader, start=2):
            raw_isbn = row.get("isbn13", "")
            isbn = normalize_isbn(raw_isbn)

            if not isbn:
                errors.append(
                    {
                        "isbn": raw_isbn,
                        "error_type": "empty_isbn",
                        "message": f"{row_number}행 ISBN이 비어 있습니다.",
                    }
                )
                continue

            if len(isbn) not in {10, 13}:
                errors.append(
                    {
                        "isbn": isbn,
                        "error_type": "invalid_length",
                        "message": (
                            f"{row_number}행 ISBN 길이가 "
                            f"{len(isbn)}자리입니다."
                        ),
                    }
                )
                continue

            if isbn in seen:
                continue

            seen.add(isbn)
            isbns.append(isbn)

    return isbns, errors


def get_identifier(
    identifiers: list[dict[str, Any]],
    identifier_type: str,
) -> str:
    """Google Books 응답에서 ISBN을 찾는다."""
    for identifier in identifiers:
        if identifier.get("type") == identifier_type:
            return normalize_isbn(
                str(identifier.get("identifier", ""))
            )

    return ""


def find_exact_result(
    items: list[dict[str, Any]],
    searched_isbn: str,
) -> dict[str, Any] | None:
    """검색한 ISBN과 정확히 일치하는 책만 반환한다."""
    for item in items:
        volume_info = item.get("volumeInfo", {})

        identifiers = volume_info.get(
            "industryIdentifiers",
            [],
        )

        isbn13 = get_identifier(
            identifiers,
            "ISBN_13",
        )

        isbn10 = get_identifier(
            identifiers,
            "ISBN_10",
        )

        if searched_isbn in {isbn13, isbn10}:
            return item

    return None


def fetch_book(
    isbn: str,
) -> tuple[dict[str, Any] | None, str]:
    """Google Books API에서 ISBN으로 책을 검색한다."""
    params = {
        "q": f"isbn:{isbn}",
        "maxResults": 5,
    }

    if API_KEY:
        params["key"] = API_KEY

    response = requests.get(
        API_URL,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    items = response.json().get("items", [])

    if not items:
        return None, "not_found"

    item = find_exact_result(items, isbn)

    if item is None:
        return None, "isbn_mismatch"

    return item, "success"


def join_list(value: Any) -> str:
    """목록 값을 | 구분 문자열로 바꾼다."""
    if not isinstance(value, list):
        return ""

    return " | ".join(
        str(item).strip()
        for item in value
        if str(item).strip()
    )


def get_cover_url(volume_info: dict[str, Any]) -> str:
    """Google Books 표지 주소를 반환한다."""
    image_links = volume_info.get("imageLinks", {})

    url = (
        image_links.get("thumbnail")
        or image_links.get("smallThumbnail")
        or ""
    )

    return str(url).replace(
        "http://",
        "https://",
        1,
    )


def make_book_row(
    item: dict[str, Any],
) -> dict[str, Any]:
    """Google Books 응답을 books 테이블 컬럼에 맞춘다."""
    volume_info = item.get("volumeInfo", {})

    identifiers = volume_info.get(
        "industryIdentifiers",
        [],
    )

    now = datetime.now(timezone.utc).isoformat()

    return {
        "book_id": str(uuid.uuid4()),
        "isbn13": get_identifier(
            identifiers,
            "ISBN_13",
        ),
        "isbn10": get_identifier(
            identifiers,
            "ISBN_10",
        ),
        "google_books_id": item.get("id", ""),
        "title": volume_info.get("title", ""),
        "subtitle": volume_info.get("subtitle", ""),
        "authors": join_list(
            volume_info.get("authors")
        ),
        "translator": "",
        "publisher": volume_info.get("publisher", ""),
        "published_date": volume_info.get(
            "publishedDate",
            "",
        ),
        "description": volume_info.get(
            "description",
            "",
        ),
        "categories": join_list(
            volume_info.get("categories")
        ),
        "page_count": volume_info.get(
            "pageCount",
            "",
        ),
        "language_code": volume_info.get(
            "language",
            "",
        ),
        "cover_url": get_cover_url(volume_info),
        "preview_url": volume_info.get(
            "previewLink",
            "",
        ),
        "info_url": volume_info.get(
            "infoLink",
            "",
        ),
        "data_source": "google_books",
        "created_at": now,
        "updated_at": now,
    }


def write_csv(
    file_path: Path,
    rows: list[dict[str, Any]],
    columns: list[str],
) -> None:
    """CSV 파일을 저장한다."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with file_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    try:
        isbns, errors = read_isbns()
    except (FileNotFoundError, ValueError) as error:
        print(f"[실패] {error}")
        return

    books: list[dict[str, Any]] = []

    for isbn in isbns:
        print(f"ISBN 조회: {isbn}")

        try:
            item, status = fetch_book(isbn)

            if status == "not_found":
                errors.append(
                    {
                        "isbn": isbn,
                        "error_type": "not_found",
                        "message": (
                            "Google Books 검색 결과가 없습니다."
                        ),
                    }
                )
                print("  → 검색 결과 없음")

            elif status == "isbn_mismatch":
                errors.append(
                    {
                        "isbn": isbn,
                        "error_type": "isbn_mismatch",
                        "message": (
                            "검색 결과의 ISBN이 입력 ISBN과 "
                            "일치하지 않습니다."
                        ),
                    }
                )
                print("  → ISBN 불일치")

            elif item is not None:
                book = make_book_row(item)
                books.append(book)

                print(
                    f"  → 성공: {book['title']}"
                )

        except requests.HTTPError as error:
            status_code = (
                error.response.status_code
                if error.response is not None
                else ""
            )

            errors.append(
                {
                    "isbn": isbn,
                    "error_type": "http_error",
                    "message": f"HTTP 오류: {status_code}",
                }
            )

            print(f"  → HTTP 오류: {status_code}")

        except requests.RequestException as error:
            errors.append(
                {
                    "isbn": isbn,
                    "error_type": "request_error",
                    "message": str(error),
                }
            )

            print(f"  → 요청 오류: {error}")

        except Exception as error:
            errors.append(
                {
                    "isbn": isbn,
                    "error_type": type(error).__name__,
                    "message": str(error),
                }
            )

            print(f"  → 오류: {error}")

        time.sleep(0.3)

    write_csv(
        OUTPUT_FILE,
        books,
        BOOK_COLUMNS,
    )

    write_csv(
        ERROR_FILE,
        errors,
        ERROR_COLUMNS,
    )

    print()
    print(f"성공: {len(books)}건")
    print(f"실패: {len(errors)}건")
    print(f"도서 파일: {OUTPUT_FILE}")
    print(f"오류 파일: {ERROR_FILE}")


if __name__ == "__main__":
    main()