import sqlite3

conn = sqlite3.connect("iot_data.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS lecturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    temperature REAL,
    humidity REAL,
    timestamp TEXT,
    estado TEXT
)
""")

conn.commit()
conn.close()

print("Base de datos y tabla creadas correctamente")