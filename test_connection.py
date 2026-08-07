from apps.api.app.database.connection import get_connection

conn = get_connection()

print(conn.sql("SELECT version();").fetchall())

conn.close()