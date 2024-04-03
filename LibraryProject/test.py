import psycopg2
from contextlib import contextmanager

@contextmanager
def connection_pstgr():
    conn = psycopg2.connect(
        dbname="libraryproject",
        host="127.0.0.1",
        user="postgres",
        password="password",
        port="5432"
    )
    cursor = conn.cursor()
    try:
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()

with connection_pstgr() as (conn, cursor):
    cursor.execute("SELECT * FROM Users")
    searched_user = cursor.fetchone()
    print(searched_user)

print(cursor.closed)
print(conn.closed)
# Now the connection and cursor are automatically closed after exiting the with block
