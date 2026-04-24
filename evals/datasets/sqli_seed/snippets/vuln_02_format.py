# ruff: noqa
def delete_order(conn, order_id):
    cur = conn.cursor()
    sql = "DELETE FROM orders WHERE id = {}".format(order_id)
    cur.execute(sql)
    conn.commit()
