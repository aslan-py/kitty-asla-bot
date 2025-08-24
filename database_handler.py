import sqlite3
from datetime import datetime
from typing import List, Tuple
import logging

from config import DATABASE_NAME

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_user_exists(username: str) -> bool:
    """
    Проверяет, существует ли пользователь в базе.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        query = "SELECT id, name FROM logins WHERE name = ?"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        conn.close()

        if result:
            logger.info(
                f'Пользователь {username} найден в базе (ID: {result[0]})')
            return True
        else:
            logger.warning(f'❌ Пользователь {username} НЕ найден в базе')
            return False

    except Exception as e:
        logger.error(f"Ошибка проверки пользователя {username}: {e}")
        return False


def get_expenses_statistics(period_data: dict) -> List[Tuple]:
    """
    Получает статистику трат за указанный период.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        # даты сначала конвертируем из человекочитаемого формата в формат SQL
        start_date = (datetime.strptime(period_data['start_date'],
                                        '%d.%m.%Y').strftime('%Y-%m-%d'))
        end_date = (datetime.strptime(period_data['end_date'],
                                      '%d.%m.%Y').strftime('%Y-%m-%d'))

        logger.info(f'  ПОИСК СТАТИСТИКИ:')
        logger.info(f'   Username: {period_data['username']}')
        logger.info(f'   Период: {start_date} до {end_date}')

        # ТЕСТ 1: Простой запрос без JOIN
        test_query1 = "SELECT * FROM products WHERE created_at BETWEEN ? AND ?"
        cursor.execute(
            test_query1, (f'{start_date} 00:00:00', f'{end_date} 23:59:59'))
        test_results1 = cursor.fetchall()
        logger.info(
            f'   ТЕСТ 1 - Простой поиск по дате: {len(test_results1)} записей')

        # ТЕСТ 2: Поиск по username без даты
        test_query2 = """
        SELECT p.* FROM products p
        JOIN logins l ON p.login_id = l.id
        WHERE l.name = ?
        """
        cursor.execute(test_query2, (period_data['username'],))
        test_results2 = cursor.fetchall()
        logger.info(
            f'   ТЕСТ 2 - Поиск по пользователю: {len(test_results2)} записей')

        # ТЕСТ 3: Полный запрос
        query = """
        SELECT
            c.name as category,
            SUM(p.price) as total_amount,
            COUNT(p.id) as transactions_count
        FROM products p
        JOIN logins l ON p.login_id = l.id
        JOIN categories c ON p.category_id = c.id
        WHERE l.name = ?
        AND date(p.created_at) BETWEEN ? AND ?
        GROUP BY c.name
        ORDER BY total_amount DESC
        """

        cursor.execute(query, (period_data['username'], start_date, end_date))
        results = cursor.fetchall()

        logger.info(f' РЕЗУЛЬТАТЫ ПОИСКА: {len(results)}')

        conn.close()
        return results

    except Exception as e:
        logger.error(f"❌ Ошибка в get_expenses_statistics: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def get_total_statistics(period_data: dict) -> dict:
    """
    Получает общую статистику за период.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        start_date = (datetime.strptime(period_data['start_date'],
                                        '%d.%m.%Y').strftime('%Y-%m-%d'))
        end_date = (datetime.strptime(period_data['end_date'],
                                      '%d.%m.%Y').strftime('%Y-%m-%d'))

        query = """
        SELECT
            SUM(p.price) as total_amount,
            COUNT(p.id) as transactions_count,
            AVG(p.price) as average_transaction,
            (SELECT c.name FROM products p2
             JOIN categories c ON p2.category_id = c.id
             JOIN logins l ON p2.login_id = l.id
             WHERE l.name = ? AND date(p2.created_at) BETWEEN ? AND ?
             GROUP BY c.name ORDER BY SUM(p2.price) DESC LIMIT 1) as top_category
        FROM products p
        JOIN logins l ON p.login_id = l.id
        WHERE l.name = ?
        AND date(p.created_at) BETWEEN ? AND ?
        """

        cursor.execute(query, (
            period_data['username'], start_date, end_date,
            period_data['username'], start_date, end_date
        ))

        result = cursor.fetchone()
        conn.close()

        if result and result[0] is not None:
            return {
                'total_amount': result[0] or 0,
                'top_category': result[3] or 'Нет данных'
            }
        else:
            return {
                'total_amount': 0,
                'top_category': 'Нет данных'
            }

    except Exception as e:
        logger.error(f"Ошибка получения общей статистики: {e}")
        return {}


def format_statistics_message(
        period_data: dict, statistics: List[Tuple], total_stats: dict) -> str:
    """
    Форматирует статистику в красивое сообщение для Telegram.
    """
    if not statistics or total_stats.get('total_amount', 0) == 0:
        return '📊 За выбранный период трат не найдено.'

    message = f'📊 *Статистика за период:*\n'
    message += f'С {period_data['start_date']} по {period_data['end_date']}\n\n'

    message += f'💵 *Общая сумма:* {total_stats['total_amount']} руб.\n'
    message += f'🏆 *Топ категория:* {total_stats['top_category']}\n\n'

    message += '*📋 Детали по категориям:*\n'

    for i, (category, amount, count) in enumerate(statistics, 1):
        if total_stats['total_amount'] > 0:
            percentage = (amount / total_stats['total_amount'] * 100)
        else:
            percentage = 0
        message += f'{i}. {category}: {amount} руб. ({count} шт.) - {percentage:.1f}%\n'

    return message
