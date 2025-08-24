"""Функция для создания БД. Используется единожды в самом начале."""

import sqlite3 as sq

from config import DATABASE_NAME


def create_base():
    """Создаем базу данных."""
    con = sq.connect(DATABASE_NAME)
    cur = con.cursor()

    logins_quary = '''
    CREATE TABLE IF NOT EXISTS logins(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    '''
    category_quary = '''
    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    '''
    products_quary = '''
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        price INTEGER NOT NULL,
        login_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(login_id) REFERENCES logins(id),
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )
    '''
    cur.execute(logins_quary)
    cur.execute(category_quary)
    cur.execute(products_quary)

    categories_data = [
        ('food', 'Продукты питания'),
        ('restaurants', 'Рестораны и кафе'),
        ('entertainment', 'Развлечения'),
        ('transport', 'Транспорт'),
        ('utilities', 'Коммунальные услуги'),
        ('shopping', 'Шоппинг'),
        ('medicine', 'Врачи и клиники'),
        ('pharmacy', 'Аптеки'),
        ('education', 'Образование'),
        ('other', 'Прочее'),
        ('home', 'Для дома'),
        ('auto', 'Авто'),
        ('beauty', 'Косметика и красота'),
        ('travels', 'Путешевствия'),
        ('credits', 'Кредиты'),
    ]

    for category_name, description in categories_data:
        try:
            cur.execute('INSERT INTO categories(name, description) VALUES(?, ?)',
                        (category_name, description))
        except Exception as e:
            print(f'Ошибка при добавлении категории  {e}')
    con.commit()
    con.close()

    print('База данных создана')
# create_base()