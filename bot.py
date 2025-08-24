"""
Основная логика работы бота.
"""
import datetime
import time
import os
import log
import logging

from datetime import timedelta
from dotenv import load_dotenv
from telebot import TeleBot, types

from database import base_insert
from database_handler import (get_expenses_statistics, get_total_statistics,
                              format_statistics_message, check_user_exists)
from config import TIME_TO_CLEAR
from cat_api import get_cat_img

logging.getLogger("telebot").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

load_dotenv()

secret_token = os.getenv('TOKEN')
bot = TeleBot(token=secret_token)

bot.set_my_commands([
    types.BotCommand("/start", "🐆 Начать работу с ботом"),
    types.BotCommand("/help", "❓ Показать справку"),
    types.BotCommand("/stats", "💸 Показать статистику трат"),
    types.BotCommand("/cat", "🐱‍🚀 Показать котика"),
])


user_status = {}
for_user_stats = {}


@bot.message_handler(commands=['cat'])
def cat(message):
    new_cat = get_cat_img()
    if new_cat:
        bot.send_photo(message.chat.id, new_cat)
    else:
        bot.send_message(
            message.chat.id, '😾 попробуй позже , я не смог получить котика')


@bot.message_handler(commands=['start'])
def handle_start(message):

    user_status[message.chat.id] = {
        'login': message.chat.username,
        'active': True,
        'time': time.time()
    }

    bot.send_message(
        chat_id=message.chat.id,
        text=f'✅ Привет, {message.chat.first_name}! Теперь я буду '
            f'сохранять твои траты.\n\n'
            f'Просто присылай мне сообщения в формате:\n'
            f'<code>продукт сумма</code>\n\n'
            f'Пример: <code>мясо 1500</code>\n\n'
            f'📋 *Команды доступны через меню:*\n'
            f'• Нажми на иконку "︙" слева от поля ввода\n'
            f'• Или просто напиши /help, /stats',
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()

    )
    logging.debug('Сообщение функции handle_start отправлено')


@bot.message_handler(commands=['help'])
def handle_help(message):
    text = '''
   👋 *Привет, я kitty_asla_bot!*

🐱 *Моя задача* - помочь тебе вести учет твоих затрат.

📋 *Алгоритм действий:*

1️⃣ Введи команду */start* чтобы начать
2️⃣ Напиши одним сообщением:
   *[что купил] [сколько потратил]*

🍖 *Пример:*
   `мясо 1500`
   `кафе 1200`
   `транспорт 500`

💡 *Совет:* Я автоматически определю категорию твоих трат!

📊 *Доступные команды:*
/start - начать работу
/help - показать справку
/stats - показать статистику
/cat - просто картинка котика
'''

    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        parse_mode='Markdown'
    )
    logging.debug('Сообщение функции handle_help отправлено')


def create_stats_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("📅 Произвольный период", callback_data="stats_custom"),
        types.InlineKeyboardButton("📆 Неделя", callback_data="stats_week"),
        types.InlineKeyboardButton("📊 Месяц", callback_data="stats_month"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="stats_cancel")
    ]
    keyboard.add(buttons[0])
    keyboard.add(buttons[1], buttons[2])
    keyboard.add(buttons[3])
    return keyboard


@bot.message_handler(commands=['stats'])
def handle_stats(message):
    """Обработчик команды /stats"""
    chat_id = message.chat.id
    username = message.chat.username
    logging.debug('Запрос статистики')

    remove_keyboard = types.ReplyKeyboardRemove()

    # Проверяем есть ли пользователь в базе
    if not check_user_exists(username):
        bot.send_message(
            chat_id,
            "❌ Вы еще не добавляли траты!\n"
            "Сначала добавьте записи через команду /start",
            reply_markup=remove_keyboard
        )
        return

    for_user_stats[chat_id] = {
        'username': username,
        'state': 'stats_menu'
    }
    bot.send_message(
        chat_id,
        "📊 *Выберите период для статистики:*",
        parse_mode='Markdown',
        reply_markup=create_stats_keyboard()
    )
    logging.debug('Показали в ТГ окно выбора периода')


@bot.callback_query_handler(func=lambda call: call.data.startswith('stats_'))
def handle_stats_callback(call):
    """Обработчик callback от кнопок статистики"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    username = call.message.chat.username

    if call.data == 'stats_custom':
        bot.edit_message_text(
            "📅 *Выберите произвольный период:*\n\n"
            "Пришлите даты в формате:\n"
            "`ДД.ММ.ГГГГ-ДД.ММ.ГГГГ`\n"
            "Например: `01.01.2024-31.01.2024`",
            chat_id,
            message_id,
            parse_mode='Markdown'
        )
        for_user_stats[chat_id] = {
            'username': username,
            'state': 'waiting_dates'
        }
        logging.debug('Выбор произвольного периода')

    elif call.data == 'stats_week':
        end_date = datetime.date.today()
        start_date = end_date - timedelta(days=7)
        period_data = {
            'username': username,
            'start_date': start_date.strftime('%d.%m.%Y'),
            'end_date': end_date.strftime('%d.%m.%Y'),
            'period_type': 'week'
        }
        bot.edit_message_text(
            f'📆 *Статистика за неделю:*\n'
            f'С {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}',
            chat_id,
            message_id,
            parse_mode='Markdown'
        )
        logging.debug('Выбор статистики за неделю')
        process_statistics(chat_id, period_data)

    elif call.data == 'stats_month':
        today = datetime.date.today()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = (today.replace(year=today.year + 1,
                                      month=1, day=1) - timedelta(days=1))
        else:
            end_date = (today.replace(month=today.month + 1, day=1) -
                        timedelta(days=1))
        period_data = {
            'username': username,
            'start_date': start_date.strftime('%d.%m.%Y'),
            'end_date': end_date.strftime('%d.%m.%Y'),
            'period_type': 'month'
        }
        bot.edit_message_text(
            f'📊 *Статистика за месяц:*\n'
            f'С {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}',
            chat_id,
            message_id,
            parse_mode='Markdown'
        )
        logging.debug('Выбор статистики за месяц')
        process_statistics(chat_id, period_data)

    elif call.data == 'stats_back':
        bot.edit_message_text(
            '📊 *Выберите период для статистики:*',
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=create_stats_keyboard()
        )
        for_user_stats[chat_id]['state'] = 'stats_menu'
        logging.debug('Возврат внутри выбора периода статистики')

    elif call.data == 'stats_cancel':
        bot.delete_message(chat_id, message_id)
        if chat_id in for_user_stats:
            del for_user_stats[chat_id]
        logging.debug('Отмена выбора статистики')


@bot.message_handler(
        func=lambda message:
        for_user_stats.get(message.chat.id, {}).get('state') == 'waiting_dates'
)
def handle_custom_dates(message):
    """Обработчик произвольного периода"""
    chat_id = message.chat.id
    text = message.text.strip()
    username = message.chat.username
    try:
        if '-' in text and text.count('.') == 4:
            start_str, end_str = text.split('-')
            start_date = datetime.datetime.strptime(start_str, '%d.%m.%Y').date()
            end_date = datetime.datetime.strptime(end_str, '%d.%m.%Y').date()
            if start_date > end_date:
                bot.send_message(
                    chat_id, "❌ Дата начала не может быть позже даты окончания!")
                return
            period_data = {
                'username': for_user_stats[chat_id]['username'],
                'start_date': start_date.strftime('%d.%m.%Y'),
                'end_date': end_date.strftime('%d.%m.%Y'),
                'period_type': 'custom'
            }
            bot.send_message(
                chat_id,
                f'📅 *Выбран период:*\n'
                f'С {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}',
                parse_mode='Markdown'
            )
            process_statistics(chat_id, period_data)
            if chat_id in for_user_stats:
                del for_user_stats[chat_id]
        else:
            bot.send_message(
                chat_id,
                '❌ Неверный формат!\nИспользуйте: ДД.ММ.ГГГГ-ДД.ММ.ГГГГ\nПример: `01.01.2024-31.01.2024`',
                parse_mode='Markdown'
            )
    except ValueError:
        bot.send_message(chat_id, '❌ Ошибка в формате даты! Проверьте правильность ввода.')
        logging.error('Ошибка в формате даты!')


def process_statistics(chat_id, period_data):
    """Обрабатывает статистику и отправляет результат"""
    try:
        # Проверяем есть ли пользователь в базе
        if not check_user_exists(period_data['username']):
            bot.send_message(
                chat_id,
                '❌ Пользователь не найден в базе данных.\n'
                'Возможно, вы еще не добавляли траты.'
            )
            return

        statistics = get_expenses_statistics(period_data)
        total_stats = get_total_statistics(period_data)
        message = format_statistics_message(period_data, statistics, total_stats)
        bot.send_message(chat_id, message, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Ошибка обработки статистики: {e}")
        bot.send_message(chat_id, "❌ Произошла ошибка при получении статистики.")


@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id

    if message.text in ['/help', '/stats', '/start']:
        return
    if chat_id not in user_status or not user_status[chat_id]['active']:
        bot.send_message(
            chat_id=chat_id,
            text='❌ Сначала нажми /start чтобы начать.\nИли /help для подсказки'
        )
        logging.debug(
            'Пользователь незарегистрирован - отказ отработал штатно')
        return

    if (user_status[chat_id]['active'] and
        time.time() - user_status[chat_id]['time'] > TIME_TO_CLEAR):
        del user_status[chat_id]
        bot.send_message(
            chat_id=chat_id, text='🦘Сессия закрылась, нажми повторно /start')
        logging.debug('Сообщение о закрытии сессии отправилось')
        return

    if user_status[chat_id]['active']:
        user_data = {
            'login': message.chat.username,
            'staf': message.text,
        }
    try:
        base_insert(user_data)
        bot.send_message(chat_id=chat_id, text='✅ Данные сохраняю в базу!')
        logging.debug(f'Данные в базу сохранены - сообщение в ТГ {user_data}')
    except Exception as e:
        logging.error(f'Ошибка сохранения в базу {e}')
        bot.send_message(
            chat_id=chat_id,
            text='💀 Что-то пошло не так, я не смог сохранить данные, попробуй еще раз'
        )


if __name__ == "__main__":
    logging.info("Бот запущен")
    print('Бот запущен!')
    bot.polling(
        none_stop=True,
        timeout=10,
        interval=2
    )
