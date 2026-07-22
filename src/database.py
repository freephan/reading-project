from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        raise RuntimeError(
            ".env 파일에 DATABASE_URL이 설정되지 않았습니다."
        )

    return database_url


def create_database_engine() -> Engine:
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        echo=False,
    )


engine = create_database_engine()