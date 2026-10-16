"""資料庫層：
- 有設定 DATABASE_URL（Supabase Postgres）→ 使用 Postgres（雲端、永久保存）
- 沒設定 → 使用本地 SQLite clove.db（本地測試用）
對外介面維持 sqlite3 風格：conn.execute(sql_with_?, params) / fetchone / fetchall / commit / lastrowid
"""
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_PG = DATABASE_URL.startswith("postgres")
DB_PATH = Path(__file__).parent / "clove.db"


class _PGCursor:
    def __init__(self, cur, lastrowid=None):
        self._cur = cur
        self.lastrowid = lastrowid

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()


class _PGConn:
    """把 sqlite 風格的 SQL（? 佔位符）轉成 psycopg（%s）"""

    def __init__(self):
        import psycopg
        from psycopg.rows import dict_row
        # prepare_threshold=None：相容 Supabase 連線池（pooler）
        self._conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, prepare_threshold=None)

    def execute(self, sql, params=()):
        sql = sql.replace("?", "%s")
        is_insert = sql.lstrip().upper().startswith("INSERT")
        if is_insert and "RETURNING" not in sql.upper():
            sql = sql.rstrip().rstrip(";") + " RETURNING id"
        cur = self._conn.cursor()
        cur.execute(sql, tuple(params) if params else None)
        lastrowid = None
        if is_insert:
            row = cur.fetchone()
            lastrowid = row["id"] if row else None
        return _PGCursor(cur, lastrowid)

    def cursor(self):
        return self

    def fetchone(self):  # 給 init_db 的 cur 風格用不到，保留相容
        raise NotImplementedError

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def get_db():
    if USE_PG:
        return _PGConn()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


if USE_PG:
    PK = "SERIAL PRIMARY KEY"
    NOW = "(to_char(now() AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS'))"
else:
    PK = "INTEGER PRIMARY KEY AUTOINCREMENT"
    NOW = "(datetime('now','localtime'))"

SCHEMA = [
    f"""
    CREATE TABLE IF NOT EXISTS users (
        id {PK},
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'member',
        points INTEGER NOT NULL DEFAULT 0,
        created_at TEXT DEFAULT {NOW}
    )""",
    f"""
    CREATE TABLE IF NOT EXISTS pools (
        id {PK},
        name TEXT NOT NULL,
        description TEXT,
        image_url TEXT,
        intro_type TEXT DEFAULT 'image',
        cost_single INTEGER NOT NULL DEFAULT 100,
        cost_ten INTEGER NOT NULL DEFAULT 900,
        total_quantity INTEGER NOT NULL DEFAULT 0,
        remaining_quantity INTEGER NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT {NOW}
    )""",
    f"""
    CREATE TABLE IF NOT EXISTS cards (
        id {PK},
        pool_id INTEGER NOT NULL REFERENCES pools(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        image_url TEXT,
        total_quantity INTEGER NOT NULL DEFAULT 0,
        remaining_quantity INTEGER NOT NULL DEFAULT 0,
        original_probability REAL DEFAULT 0,
        created_at TEXT DEFAULT {NOW}
    )""",
    f"""
    CREATE TABLE IF NOT EXISTS draw_records (
        id {PK},
        user_id INTEGER NOT NULL REFERENCES users(id),
        pool_id INTEGER NOT NULL REFERENCES pools(id),
        card_id INTEGER REFERENCES cards(id),
        draw_type TEXT NOT NULL,
        cost_points INTEGER NOT NULL,
        result_json TEXT,
        created_at TEXT DEFAULT {NOW}
    )""",
    f"""
    CREATE TABLE IF NOT EXISTS transactions (
        id {PK},
        user_id INTEGER NOT NULL REFERENCES users(id),
        type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        balance_after INTEGER NOT NULL,
        note TEXT,
        operator_id INTEGER,
        created_at TEXT DEFAULT {NOW}
    )""",
]


def _ensure_user(conn, username, email, password, role, points):
    import bcrypt
    if conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
        return
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT INTO users (username, email, password_hash, role, points) VALUES (?, ?, ?, ?, ?)",
        (username, email, hashed, role, points),
    )


def init_db():
    conn = get_db()
    for stmt in SCHEMA:
        conn.execute(stmt)

    # 管理員帳號：密碼由環境變數 ADMIN_PASSWORD 設定（本地未設定時預設 admin123）
    admin_pw = os.getenv("ADMIN_PASSWORD") or "admin123"
    _ensure_user(conn, os.getenv("ADMIN_USERNAME") or "admin", "admin@clove.local", admin_pw, "admin", 0)

    # 測試會員：SEED_TEST_USER=true 才建立（本地預設建立）
    seed = os.getenv("SEED_TEST_USER", "false" if USE_PG else "true").lower() == "true"
    if seed:
        _ensure_user(conn, "user", "user@clove.local", "user123", "member", 10000)

    conn.commit()
    conn.close()
    print(f"資料庫初始化完成（{'Postgres' if USE_PG else 'SQLite'}）")


if __name__ == "__main__":
    init_db()
