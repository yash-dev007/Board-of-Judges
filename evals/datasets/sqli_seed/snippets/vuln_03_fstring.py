import sqlite3


def search_products(conn: sqlite3.Connection, term: str) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(f"SELECT id, name FROM products WHERE name LIKE '%{term}%'")
    return cur.fetchall()
