def save_preference(conn, user_id: int, pref: str) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO prefs (user_id, value) VALUES (%s, %s)", (user_id, pref)
    )
    conn.commit()


def apply_preference(conn, user_id: int) -> list:
    cur = conn.cursor()
    cur.execute("SELECT value FROM prefs WHERE user_id = %s", (user_id,))
    (pref,) = cur.fetchone()
    cur.execute("SELECT * FROM items WHERE category = '%s'" % pref)
    return cur.fetchall()
