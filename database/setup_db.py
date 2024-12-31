# database/setup_db.py
import sqlite3

def setup_database():
    connection = sqlite3.connect("database/chat_history.db")
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        protocol TEXT NOT NULL,
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    connection.commit()
    connection.close()

if __name__ == "__main__":
    setup_database()
