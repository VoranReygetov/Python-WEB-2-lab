import psycopg2
from contextlib import contextmanager
import json
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
    columns = [desc[0] for desc in cursor.description]
    print(searched_user[0])
    book_dict = dict(zip(columns, searched_user))
    inserted_book_json = json.dumps(book_dict)
print(cursor.closed)
print(conn.closed)
print(inserted_book_json)
# Now the connection and cursor are automatically closed after exiting the with block
