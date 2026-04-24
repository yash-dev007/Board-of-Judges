def find_user(conn, name: str):
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM users WHERE name = %s", (name,))
    return cur.fetchall()
