from __future__ import annotations

import os
import sys

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace(
    "postgresql+psycopg://",
    "postgresql://",
)

if len(sys.argv) != 2:
    print("사용법: python src/run_sql.py <sql파일>")
    sys.exit(1)

sql_file = sys.argv[1]

with open(sql_file, "r", encoding="utf-8") as f:
    sql = f.read()

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()

print("실행 완료!")