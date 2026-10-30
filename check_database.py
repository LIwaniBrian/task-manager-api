import sqlite3

connection = sqlite3.connect("tasks.db")

tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Tables found:", tables)

for (table_name,) in tables:
    print(f"\nTable: {table_name}")

    columns = connection.execute(
        f'PRAGMA table_info("{table_name}")'
    ).fetchall()

    print("Columns:", columns)

    records = connection.execute(
        f'SELECT COUNT(*) FROM "{table_name}"'
    ).fetchone()

    print("Number of records:", records[0])

connection.close()
