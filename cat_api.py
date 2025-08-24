import requests
import log
import logging

from config import URL


def get_cat_img():
    try:
        response = requests.get(URL, timeout=10)
        if response.status_code != 200:
            logging.error('Ошибка при запросе к API котиков')
            return False

        data = response.json()

        if data and isinstance(data, list) and len(data) > 0:
            random_cat = data[0].get('url')
            if random_cat:
                return random_cat
            else:
                logging.error('URL котика не найден в ответе')
                return False
        else:
            logging.error('API вернуло пустой ответ')
            return False
    except Exception as e:
        logging.error(f'Ошибка API: {e}')
        return False
