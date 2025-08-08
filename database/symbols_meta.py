import sqlite3
import os
from datetime import datetime

CENTRAL_DB_PATH = "database/symbols_meta.db"


def connect_central():
    os.makedirs("database", exist_ok=True)
    return sqlite3.connect(CENTRAL_DB_PATH)


def initialize_central_db():
    conn = connect_central()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS symbols (
            symbol TEXT PRIMARY KEY,
            description TEXT,
            db_path TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            last_updated TEXT
        )
    ''')
    conn.commit()
    conn.close()


def register_symbol(symbol: str, db_path: str, description: str = ""):
    """
    ثبت یا به‌روزرسانی نماد در دیتابیس مرکزی
    """
    conn = connect_central()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO symbols (symbol, description, db_path, is_active, last_updated)
        VALUES (?, ?, ?, 1, ?)
    ''', (
        symbol,
        description,
        db_path,
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    ))
    conn.commit()
    conn.close()


def get_all_registered_symbols(active_only: bool = True):
    conn = connect_central()
    cursor = conn.cursor()

    if active_only:
        cursor.execute("SELECT symbol FROM symbols WHERE is_active = 1")
    else:
        cursor.execute("SELECT symbol FROM symbols")

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]


def get_db_path_for_symbol(symbol: str):
    conn = connect_central()
    cursor = conn.cursor()
    cursor.execute("SELECT db_path FROM symbols WHERE symbol = ?", (symbol,))
    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None
