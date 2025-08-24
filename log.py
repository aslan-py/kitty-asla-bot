"""Правила логирования."""
import logging
from logging.handlers import RotatingFileHandler


# Получаем корневой логгер
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Создаем обработчик с ротацией
handler = RotatingFileHandler(
    filename='main.log',
    maxBytes=5000000,    # 5 MB
    backupCount=3,       # 3 backup files
    encoding='utf-8',
    mode='a'
)

# Настраиваем формат как в basicConfig
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s '
    '- %(filename)s:%(lineno)d - %(funcName)s'
)
handler.setFormatter(formatter)

# Очищаем существующие обработчики и добавляем наш
root_logger.handlers.clear()
root_logger.addHandler(handler)
