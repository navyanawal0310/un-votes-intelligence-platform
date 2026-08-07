from apps.api.app.database.warehouse import initialize_warehouse
from apps.api.app.database.connection import get_connection

initialize_warehouse()

conn = get_connection()

print(conn.sql("SHOW TABLES").fetchall())

conn.close()