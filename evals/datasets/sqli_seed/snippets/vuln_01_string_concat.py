def find_user(conn, name):
    """Lookup a user by name. UNTRUSTED INPUT."""
    cur = conn.cursor()
    sql = "SELECT id, email FROM users WHERE name = '" + name + "'"
    cur.execute(sql)
    return cur.fetchall()
