import sqlite3

# Подключение к базе
conn = sqlite3.connect("faceid.db")
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    photo BLOB NOT NULL
)
''')

# Создание таблицы посещений
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL
)
''')

# Сохранение и закрытие
conn.commit()
conn.close()
print("База данных создана!")
