from __future__ import annotations
import os
import csv
import re
import time
import uuid
from dotenv import load_dotenv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")
INPUT_FILE = BASE_DIR / "data" / "input" / "isbn_input.csv"
OUTPUT_FILE = BASE_DIR / "data" / "output" / "books.csv"
ERROR_FILE = BASE_DIR / "data" / "output" / "books_errors.csv"

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

REQUEST_TIMEOUT = 15
REQUEST_INTERVAL = 0.3
MAX_RETRIES = 3


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


def normalize_isbn(value: str) -> str:
    """
    ISBN에서 숫자와 ISBN-10의 X만 남긴다.
    """
    return re.sub(r"[^0-9Xx]", "", value or "").upper()


def validate_isbn_length(isbn: str) -> bool:
    """
    ISBN-10 또는 ISBN-13 길이인지 확인한다.
    """
    return len(isbn) in {10, 13}


def join_values(values: Any) -> str:
    """
    저자나 카테고리처럼 목록으로 제공되는 값을 문자열로 변환한다.
    """
    if not isinstance(values, list):
        return ""

    return " | ".join(
        str(value).strip()
        for value in values
        if str(value).strip()
    )


def get_identifier(
    identifiers: list[dict[str, Any]],
    identifier_type: str,
) -> str:
    """
    Google Books 응답에서 ISBN-10 또는 ISBN-13을 찾는다.
    """
    for item in identifiers:
        if item.get("type") == identifier_type:
            return normalize_isbn(
                str(item.get("identifier", ""))
            )

    return ""


def select_cover_url(image_links: dict[str, Any]) -> str:
    """
    가능한 표지 이미지 중 큰 이미지를 우선 선택한다.
    """
    priorities = [
        "extraLarge",
        "large",
        "medium",
        "small",
        "thumbnail",
        "smallThumbnail",
    ]

    for key in priorities:
        url = image_links.get(key)

        if url:
            return str(url).replace(
                "http://",
                "https://",
                1,
            )

    return ""


def select_best_result(
    items: list[dict[str, Any]],
    searched_isbn: str,
) -> dict[str, Any]:
    """
    검색한 ISBN과 정확히 일치하는 결과를 우선 선택한다.
    """
    for item in items:
        volume_info = item.get("volumeInfo", {})
        identifiers = volume_info.get(
            "industryIdentifiers",
            [],
        )

        result_isbn13 = get_identifier(
            identifiers,
            "ISBN_13",
        )
        result_isbn10 = get_identifier(
            identifiers,
            "ISBN_10",
        )

        if searched_isbn in {
            result_isbn13,
            result_isbn10,
        }:
            return item

    return items[0]


def fetch_book_data(

    isbn: str,

) -> dict[str, Any] | None:

    """

    Google Books API에서 ISBN으로 책 정보를 조회한다.

    """

    params = {
    "q": f"isbn:{isbn}",
    "maxResults": 5,
    "projection": "full",
    }

    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = requests.get(

                GOOGLE_BOOKS_API_URL,

                params=params,

                timeout=REQUEST_TIMEOUT,

            )

            response.raise_for_status()

            payload = response.json()

            items = payload.get("items", [])

            if not items:

                return None

            return select_best_result(

                items,

                isbn,

            )

        except requests.HTTPError as error:
            status_code = error.response.status_code if error.response else "알 수 없음"
            response_text = error.response.text[:500] if error.response else ""

            last_error = RuntimeError(
                f"HTTP 오류 {status_code}: {response_text}"
            )

            print(f"  → HTTP 오류: {status_code}")
            print(f"  → 응답 내용: {response_text}")

            if attempt < MAX_RETRIES:
                time.sleep(attempt * 2)

        except requests.RequestException as error:
            last_error = error

            print(f"  → 네트워크 오류: {type(error).__name__}")
            print(f"  → 상세 내용: {error}")

            if attempt < MAX_RETRIES:
                time.sleep(attempt * 2)

        except ValueError as error:
            last_error = error

            print(f"  → JSON 변환 오류: {error}")

            if attempt < MAX_RETRIES:
                time.sleep(attempt * 2)

    raise RuntimeError(

        f"Google Books API 요청 실패: {last_error}"

    )


def convert_to_book_row(
    item: dict[str, Any],
    searched_isbn: str,
) -> dict[str, Any]:
    """
    Google Books 응답을 books.csv 형식으로 변환한다.
    """
    volume_info = item.get("volumeInfo", {})

    identifiers = volume_info.get(
        "industryIdentifiers",
        [],
    )

    image_links = volume_info.get(
        "imageLinks",
        {},
    )

    isbn13 = get_identifier(
        identifiers,
        "ISBN_13",
    )

    isbn10 = get_identifier(
        identifiers,
        "ISBN_10",
    )

    if len(searched_isbn) == 13 and not isbn13:
        isbn13 = searched_isbn

    if len(searched_isbn) == 10 and not isbn10:
        isbn10 = searched_isbn

    now = datetime.now(
        timezone.utc
    ).isoformat()

    return {
        "book_id": str(uuid.uuid4()),
        "isbn13": isbn13,
        "isbn10": isbn10,
        "google_books_id": item.get("id", ""),
        "title": volume_info.get("title", ""),
        "subtitle": volume_info.get("subtitle", ""),
        "authors": join_values(
            volume_info.get("authors")
        ),
        "translator": "",
        "publisher": volume_info.get(
            "publisher",
            "",
        ),
        "published_date": volume_info.get(
            "publishedDate",
            "",
        ),
        "description": volume_info.get(
            "description",
            "",
        ),
        "categories": join_values(
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
        "cover_url": select_cover_url(
            image_links
        ),
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


def read_isbns(
    input_file: Path,
) -> list[str]:
    """
    isbn_input.csv에서 ISBN 목록을 읽고 중복을 제거한다.
    """
    if not input_file.exists():
        raise FileNotFoundError(
            f"입력 파일이 없습니다: {input_file}"
        )

    isbn_list: list[str] = []
    seen: set[str] = set()

    with input_file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if (
            not reader.fieldnames
            or "isbn13" not in reader.fieldnames
        ):
            raise ValueError(
                "isbn_input.csv에 isbn13 컬럼이 필요합니다."
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            isbn = normalize_isbn(
                row.get("isbn13", "")
            )

            if not isbn:
                continue

            if not validate_isbn_length(isbn):
                print(
                    f"[경고] {row_number}행 "
                    f"ISBN 길이 오류: {isbn}"
                )
                continue

            if isbn in seen:
                continue

            seen.add(isbn)
            isbn_list.append(isbn)

    return isbn_list


def write_csv(
    output_file: Path,
    rows: list[dict[str, Any]],
    columns: list[str],
) -> None:
    """
    CSV 파일을 UTF-8 BOM 형식으로 저장한다.
    """
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
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
    """
    ISBN 입력 파일을 읽어 books.csv를 생성한다.
    """
    try:
        isbns = read_isbns(INPUT_FILE)
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        print(f"[실패] {error}")
        return

    if not isbns:
        print("[종료] 처리할 ISBN이 없습니다.")
        return

    books: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    total_count = len(isbns)

    for index, isbn in enumerate(
        isbns,
        start=1,
    ):
        print(
            f"[{index}/{total_count}] "
            f"ISBN 조회: {isbn}"
        )

        try:
            item = fetch_book_data(isbn)

            if item is None:
                errors.append(
                    {
                        "isbn": isbn,
                        "error_type": "not_found",
                        "message": (
                            "Google Books에서 "
                            "검색 결과를 찾지 못했습니다."
                        ),
                    }
                )

                print("  → 검색 결과 없음")

            else:
                book_row = convert_to_book_row(
                    item,
                    isbn,
                )

                books.append(book_row)

                print(
                    "  → 성공: "
                    f"{book_row['title']} / "
                    f"{book_row['authors']}"
                )

        except Exception as error:
            errors.append(
                {
                    "isbn": isbn,
                    "error_type": type(error).__name__,
                    "message": str(error),
                }
            )

            print(f"  → 오류: {error}")

        time.sleep(REQUEST_INTERVAL)

    write_csv(
        OUTPUT_FILE,
        books,
        BOOK_COLUMNS,
    )

    write_csv(
        ERROR_FILE,
        errors,
        [
            "isbn",
            "error_type",
            "message",
        ],
    )

    print()
    print("처리 완료")
    print(f"성공: {len(books)}건")
    print(f"실패: {len(errors)}건")
    print(f"결과: {OUTPUT_FILE}")
    print(f"오류: {ERROR_FILE}")


if __name__ == "__main__":
    main()