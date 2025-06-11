import json
import sqlite3
from pathlib import Path

# Путь к файлу ingredients.json
json_file = Path('/home/rfflgnt/Documents/Dev/foodgram-st/data/ingredients.json')

# Путь к базе данных SQLite3
db_file = Path('db.sqlite3')

# Чтение данных из JSON-файла
with open(json_file, 'r', encoding='utf-8') as f:
    ingredients = json.load(f)

# Подключение к базе данных
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Создание таблицы (если её нет)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes_ingredient (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        measurement_unit TEXT NOT NULL
    )
''')

# Вставка данных в таблицу
for ingredient in ingredients:
    cursor.execute(
        'INSERT INTO recipes_ingredient (name, measurement_unit) VALUES (?, ?)',
        (ingredient['name'], ingredient['measurement_unit'])
    )

# Сохранение изменений и закрытие соединения
conn.commit()
conn.close()

print(f"Импортировано {len(ingredients)} ингредиентов.")