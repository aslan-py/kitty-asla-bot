
"""
Функция которая получает информацию о логине, продукте  и цене.
"""
import re
import log
import logging

from config import CATEGORY_KEYWORDS


def data_parse(data: dict) -> tuple[str, str, int, str]:
    login = data.get('login')  # получили логин.
    staf = data.get('staf')  # получили данные-на что потратили и сумму затрат.
    if not login or not staf:
        logging.error(
            'Не получили валидный словарь {login: xxx, staf: xxx}' \
            '  с пакета bot.py функции handle_text')

    splited_staf = staf.split(' ')  # распарсили данные  и смотрим отдельно.
    int_item = []
    str_item = []

    for item in splited_staf:  # проверка данных на str или int формат.
        if item.isdigit():
            int_item.append(int(item))  # складываем числа в список.
        else:
            str_item.append(item)  # складываем строки в список.
    sum_int_item = sum(int_item)
    str_item = ' '.join(str_item) if str_item else 'Пустое значение'

    # проверяем есть ли товар в категории
    category_name = 'other'
    text_lower = str_item.lower()

    for category, values in CATEGORY_KEYWORDS.items():
        for value in values:
            if re.search(value, text_lower):
                category_name = category
                break
        if category_name != 'other':  # Если нашли категорию, выходим
            break
    return login, str_item, sum_int_item, category_name
