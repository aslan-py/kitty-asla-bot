"""Сохранение распарсенных данных в БД."""
import sqlite3 as sq
import log
import logging
from typing import Optional

from data_income import data_parse
from config import DATABASE_NAME, OTHER_CATEGORY_ID


def get_category_id(cur: sq.Cursor, category_name: str) -> Optional[int]:
    """Получает ID категории по названию."""
    try:
        category_execute = cur.execute(
            'SELECT id FROM categories WHERE name = ?', (category_name,))
        category_correct = category_execute.fetchone()
        if category_correct:
            return category_correct[0]
        logging.warning(f'Категория {category_name} не найдена в базе')
        return None
    except sq.Error as error:
        logging.error(
            f'Ошибка получения category_id для {category_name}: {error}')
        return None


def get_login_id(cur: sq.Cursor, login: str) -> Optional[int]:
    """Получает ID логина, если существует."""
    try:
        login_execute = cur.execute(
            'SELECT id FROM logins WHERE name = ?', (login,))
        login_result = login_execute.fetchone()
        return login_result[0] if login_result else None
    except sq.Error as error:
        logging.error(f'Ошибка проверки логина {login}: {error}')
        return None


def insert_login(cur: sq.Cursor, login: str) -> Optional[int]:
    """Добавляет новый логин и возвращает его ID."""
    try:
        cur.execute('INSERT INTO logins(name) VALUES(?)', (login,))
        return cur.lastrowid
    except sq.Error as error:
        logging.error(f'Ошибка добавления логина {login}: {error}')
        return None


def insert_product(
        cur: sq.Cursor,
        title: str, price: int, login_id: int, category_id: int) -> bool:
    """Добавляет продукт в базу."""
    try:
        cur.execute(
            'INSERT INTO products(title, price, login_id, category_id)'
            'VALUES(?,?,?,?)',
            (title, price, login_id, category_id)
        )
        logging.debug(
            f'Добавлен продукт: {title}, цена: {price}, login_id: {login_id},'
            f' category_id: {category_id}'
        )
        return True
    except sq.Error as error:
        logging.error(f'Ошибка добавления продукта {title}: {error}')
        return False


def base_insert(data: dict) -> bool:
    """Записываем в базу логин, статью трат и цену."""
    try:
        # распарсим данные.
        login, str_item, sum_int_item, category_name = data_parse(data)
        # if not all([login, str_item, sum_int_item, category_name]):
        #     logging.warning('Недостаточно данных для сохранения')
        #     return False

        with sq.connect(DATABASE_NAME) as con:
            cur = con.cursor()
            logging.debug(f'{login} открыл соединение с базой')

            # Получаем ID категории
            category_id = get_category_id(cur, category_name)
            if category_id is None:
                category_id = OTHER_CATEGORY_ID  # ID для 'other'
                logging.info(
                    f'Используем категорию по умолчанию (ID: {category_id})')

            # Получаем или создаем логин
            login_id = get_login_id(cur, login)
            if login_id is None:
                login_id = insert_login(cur, login)
                if login_id is None:
                    logging.error(f'Не удалось создать логин {login}')
                    return False
                logging.debug(f'Создан новый логин {login} (ID: {login_id})')
            else:
                logging.debug(
                    f'Найден существующий логин {login} (ID: {login_id})')

            # Добавляем продукт
            if insert_product(
                    cur, str_item, sum_int_item, login_id, category_id):
                con.commit()
                logging.debug(f'Данные успешно сохранены для {login}')
                return True
            else:
                con.rollback()
                logging.error(f'Ошибка сохранения данных для {login}')
                return False

    except sq.Error as error:
        logging.error(f'Ошибка базы данных: {error}')
        return False
    except Exception as error:
        logging.error(f'Неожиданная ошибка в base_insert: {error}')
        return False
