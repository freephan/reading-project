from pathlib import Path

from sqlalchemy import text

from database import engine


BASE_DIR = Path(__file__).resolve().parent.parent
SQL_FILE = BASE_DIR / "sql" / "001_create_tables.sql"


def main() -> None:
    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"SQL 파일을 찾을 수 없습니다: {SQL_FILE}"
        )

    sql_script = SQL_FILE.read_text(
        encoding="utf-8"
    )

    statements = [
        statement.strip()
        for statement in sql_script.split(";")
        if statement.strip()
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

    print("데이터베이스 테이블 생성 완료")


if __name__ == "__main__":
    main()