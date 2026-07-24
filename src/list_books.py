from sqlalchemy import text

from database import engine


SELECT_BOOKS_SQL = text(
    """
    SELECT
        book_id,
        isbn13,
        title,
        authors,
        publisher,
        published_date
    FROM books
    ORDER BY created_at DESC
    """
)


def main() -> None:
    with engine.connect() as connection:
        books = connection.execute(
            SELECT_BOOKS_SQL
        ).mappings().all()

    if not books:
        print("저장된 책이 없습니다.")
        return

    print(f"저장된 책: {len(books)}권")
    print()

    for index, book in enumerate(
        books,
        start=1,
    ):
        print(f"{index}. {book['title']}")
        print(f"   ISBN: {book['isbn13']}")
        print(f"   저자: {book['authors'] or '-'}")
        print(f"   출판사: {book['publisher'] or '-'}")
        print(
            f"   출판일: "
            f"{book['published_date'] or '-'}"
        )
        print()


if __name__ == "__main__":
    main()