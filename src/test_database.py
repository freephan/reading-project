from sqlalchemy import text

from database import engine


def main() -> None:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user")
        )

        database_name, user_name = result.one()

    print(f"데이터베이스: {database_name}")
    print(f"사용자: {user_name}")
    print("연결 테스트 성공")


if __name__ == "__main__":
    main()